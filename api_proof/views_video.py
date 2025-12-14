from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django_filters.rest_framework import DjangoFilterBackend


from .models import VideoCourse, VideoModule, CourseEnrollment, VideoView
from .serializers import (
    VideoCourseSerializer, 
    VideoModuleSerializer,
    #CourseEnrollmentSerializer
)

class VideoCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les cours vidéo"""
    queryset = VideoCourse.objects.all()
    serializer_class = VideoCourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'is_free', 'instructor']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'duration_hours']
    
    def get_permissions(self):
        """Permissions différentes selon l'action"""
        if self.action in ['list', 'retrieve', 'preview_modules']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_context(self):
        """Ajouter le contexte pour les méthodes personnalisées"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Récupérer tous les modules d'un cours"""
        course = self.get_object()
        modules = course.modules.all().order_by('order')
        
        # Pour les non-inscrits, ne montrer que les previews
        if not request.user.is_authenticated:
            modules = modules.filter(is_preview=True)
        
        serializer = VideoModuleSerializer(
            modules, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """S'inscrire à un cours"""
        course = self.get_object()
        user = request.user
        
        # Vérifier si déjà inscrit
        if CourseEnrollment.objects.filter(student=user, course=course).exists():
            return Response(
                {'error': 'Déjà inscrit à ce cours'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer l'inscription
        enrollment = CourseEnrollment.objects.create(
            student=user,
            course=course,
            status='active'
        )
        
        serializer = CourseEnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Récupérer la progression dans un cours"""
        course = self.get_object()
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=request.user,
                course=course
            )
            
            # Calculer la progression réelle
            total_modules = course.modules.count()
            completed_modules = VideoView.objects.filter(
                enrollment=enrollment,
                completed=True
            ).count()
            
            progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
            
            return Response({
                'enrollment_id': enrollment.id,
                'status': enrollment.status,
                'progress_percentage': progress,
                'completed_modules': completed_modules,
                'total_modules': total_modules,
                'enrolled_at': enrollment.enrolled_at,
                'completed_at': enrollment.completed_at
            })
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Non inscrit à ce cours'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_courses(self, request):
        """Récupérer les cours de l'utilisateur connecté"""
        enrollments = CourseEnrollment.objects.filter(
            student=request.user
        ).select_related('course')
        
        courses = [enrollment.course for enrollment in enrollments]
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class VideoModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les modules vidéo"""
    queryset = VideoModule.objects.all()
    serializer_class = VideoModuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrer selon les permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated:
            # Récupérer les cours auxquels l'utilisateur est inscrit
            enrolled_courses = CourseEnrollment.objects.filter(
                student=user,
                status='active'
            ).values_list('course_id', flat=True)
            
            # Voir les modules des cours inscrits OU les previews
            queryset = queryset.filter(
                Q(course_id__in=enrolled_courses) | Q(is_preview=True)
            )
        else:
            # Pour les non connectés, seulement les previews
            queryset = queryset.filter(is_preview=True)
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def mark_watched(self, request, pk=None):
        """Marquer une vidéo comme visionnée"""
        module = self.get_object()
        user = request.user
        
        # Vérifier l'inscription
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=module.course,
                status='active'
            )
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Non inscrit à ce cours'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer ou créer le suivi de visionnage
        video_view, created = VideoView.objects.get_or_create(
            enrollment=enrollment,
            module=module,
            defaults={
                'watch_duration_seconds': module.duration_minutes * 60,
                'watched_percentage': 100,
                'completed': True
            }
        )
        
        if not created:
            video_view.watch_duration_seconds = module.duration_minutes * 60
            video_view.watched_percentage = 100
            video_view.completed = True
            video_view.save()
        
        # Mettre à jour la progression du cours
        self.update_course_progress(enrollment)
        
        return Response({
            'status': 'success',
            'message': 'Vidéo marquée comme visionnée',
            'video_view_id': video_view.id,
            'completed': video_view.completed
        })
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Mettre à jour la progression du visionnage"""
        module = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=module.course,
                status='active'
            )
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Non inscrit à ce cours'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Valider les données
        watched_percentage = request.data.get('watched_percentage', 0)
        watch_duration = request.data.get('watch_duration_seconds', 0)
        
        if not (0 <= watched_percentage <= 100):
            return Response(
                {'error': 'Pourcentage invalide (0-100)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le suivi
        video_view, created = VideoView.objects.update_or_create(
            enrollment=enrollment,
            module=module,
            defaults={
                'watched_percentage': watched_percentage,
                'watch_duration_seconds': watch_duration,
                'completed': watched_percentage >= 90  # Considéré comme complété à 90%
            }
        )
        
        # Mettre à jour la progression du cours si nécessaire
        if video_view.completed:
            self.update_course_progress(enrollment)
        
        return Response({
            'status': 'success',
            'watched_percentage': video_view.watched_percentage,
            'completed': video_view.completed
        })
    
    def update_course_progress(self, enrollment):
        """Mettre à jour la progression globale du cours"""
        total_modules = enrollment.course.modules.count()
        completed_modules = VideoView.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
        enrollment.progress_percentage = progress
        
        # Marquer comme terminé si progression à 100%
        if progress >= 100:
            enrollment.status = 'completed'
        
        enrollment.save()
    
    @action(detail=True, methods=['get'])
    def next_module(self, request, pk=None):
        """Récupérer le module suivant"""
        current_module = self.get_object()
        
        next_module = VideoModule.objects.filter(
            course=current_module.course,
            order__gt=current_module.order
        ).order_by('order').first()
        
        if next_module:
            serializer = self.get_serializer(next_module)
            return Response(serializer.data)
        
        return Response({'message': 'C\'est le dernier module'})
    
    @action(detail=True, methods=['get'])
    def previous_module(self, request, pk=None):
        """Récupérer le module précédent"""
        current_module = self.get_object()
        
        previous_module = VideoModule.objects.filter(
            course=current_module.course,
            order__lt=current_module.order
        ).order_by('-order').first()
        
        if previous_module:
            serializer = self.get_serializer(previous_module)
            return Response(serializer.data)
        
        return Response({'message': 'C\'est le premier module'})


class PublicVideoAPIView(generics.ListAPIView):
    """API publique pour les vidéos gratuites/preview"""
    permission_classes = [AllowAny]
    serializer_class = VideoModuleSerializer
    
    def get_queryset(self):
        # Récupérer seulement les vidéos en preview
        return VideoModule.objects.filter(is_preview=True).select_related('course')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CourseSearchAPIView(generics.ListAPIView):
    """Recherche de cours"""
    permission_classes = [AllowAny]
    serializer_class = VideoCourseSerializer
    
    def get_queryset(self):
        queryset = VideoCourse.objects.all()
        
        # Filtre par niveau
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)
        
        # Filtre par prix (gratuit/payant)
        is_free = self.request.query_params.get('is_free', None)
        if is_free is not None:
            queryset = queryset.filter(is_free=(is_free.lower() == 'true'))
        
        # Recherche par titre/description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Tri
        order_by = self.request.query_params.get('order_by', 'created_at')
        if order_by in ['created_at', 'price', 'duration_hours']:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context