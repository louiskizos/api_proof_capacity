# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import models

from .models import VideoCourse, VideoModule, CourseEnrollment, VideoView

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides')
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'date_joined')




class VideoModuleSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.CharField(
        source='course.instructor.get_full_name',
        read_only=True
    )
    is_enrolled = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = VideoModule
        fields = "__all__"
        read_only_fields = ['id']

    def _get_enrollment(self, request, course):
        return CourseEnrollment.objects.get(
            student=request.user,
            course=course
        )

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CourseEnrollment.objects.filter(
                student=request.user,
                course=obj.course,
                status='active'
            ).exists()
        return False

    def get_watch_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        try:
            enrollment = self._get_enrollment(request, obj.course)
            view = VideoView.objects.filter(
                enrollment=enrollment,
                module=obj
            ).first()
            return view.watched_percentage if view else 0
        except CourseEnrollment.DoesNotExist:
            return 0

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            enrollment = self._get_enrollment(request, obj.course)
            view = VideoView.objects.filter(
                enrollment=enrollment,
                module=obj
            ).first()
            return view.completed if view else False
        except CourseEnrollment.DoesNotExist:
            return False

class VideoCourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    module_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoCourse
        fields = [
            'id', 'title', 'description', 'instructor', 'instructor_name',
            'level', 'duration_hours', 'price', 'is_free', 'thumbnail_url',
            'module_count', 'total_duration', 'is_enrolled',
            'enrollment_status', 'progress_percentage',
            'created_at', 'updated_at'
        ]
    
    def get_module_count(self, obj):
        return obj.modules.count()
    
    def get_total_duration(self, obj):
        total_minutes = obj.modules.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        return total_minutes
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CourseEnrollment.objects.filter(
                student=request.user,
                course=obj
            ).exists()
        return False
    
    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(
                    student=request.user,
                    course=obj
                )
                return enrollment.status
            except:
                return None
        return None
    
    def get_progress_percentage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(
                    student=request.user,
                    course=obj
                )
                return enrollment.progress_percentage
            except:
                return 0
        return 0