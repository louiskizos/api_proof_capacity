from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import VideoCourse, CourseEnrollment, VideoModule
from .services.video_tracking import VideoTrackingService
from .services.quiz_service import QuizService
from .services.video_certification_service import VideoCertificationService
import json

class TrackVideoViewAPI(APIView):
    """API pour suivre la visualisation d'une vidéo"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            module_id = request.data.get('module_id')
            watch_duration = int(request.data.get('watch_duration', 0))
            total_duration = int(request.data.get('total_duration', 1))
            
            if not module_id:
                return Response({
                    'status': 'error',
                    'message': 'module_id requis'
                }, status=400)
            
            result = VideoTrackingService.track_video_view(
                student=request.user,
                module_id=module_id,
                watch_duration=watch_duration,
                total_duration=total_duration
            )
            
            if result['success']:
                return Response({
                    'status': 'success',
                    'data': result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=400)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class GetCourseProgressAPI(APIView):
    """API pour obtenir la progression d'un cours"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            result = VideoTrackingService.get_course_progress(
                student=request.user,
                course_id=course_id
            )
            
            if result['success']:
                return Response({
                    'status': 'success',
                    'data': result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=404)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class TakeQuizAPI(APIView):
    """API pour passer un quiz"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, quiz_id):
        try:
            answers = request.data.get('answers', {})
            
            result = QuizService.take_quiz(
                student=request.user,
                quiz_id=quiz_id,
                answers=answers
            )
            
            if result['success']:
                return Response({
                    'status': 'success',
                    'data': result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=400)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class CheckCertificationEligibilityAPI(APIView):
    """API pour vérifier l'éligibilité à la certification"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            service = VideoCertificationService()
            eligibility = service.check_eligibility_for_certification(
                student=request.user,
                course_id=course_id
            )
            
            return Response({
                'status': 'success',
                'eligible': eligibility['eligible'],
                'data': eligibility
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class RequestCertificationAPI(APIView):
    """API pour demander une certification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        try:
            service = VideoCertificationService()
            result = service.issue_certification_nft(
                student=request.user,
                course_id=course_id
            )
            
            if result['success']:
                return Response({
                    'status': 'success',
                    'data': result
                }, status=201)
            else:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=400)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class MyCertificatesAPI(APIView):
    """API pour voir ses certificats"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer toutes les inscriptions terminées
            enrollments = CourseEnrollment.objects.filter(
                student=request.user,
                status='completed'
            ).select_related('course', 'course__instructor')
            
            certificates_data = []
            
            for enrollment in enrollments:
                try:
                    certificate = enrollment.certificate
                    certificates_data.append({
                        'course_id': enrollment.course.id,
                        'course_title': enrollment.course.title,
                        'instructor': enrollment.course.instructor.email,
                        'completion_date': enrollment.completed_at,
                        'certificate_id': certificate.id,
                        'skills_verified': certificate.skills_verified,
                        'has_nft': certificate.nft is not None,
                        'nft_fingerprint': certificate.nft.fingerprint if certificate.nft else None
                    })
                except:
                    # Pas encore de certificat
                    pass
            
            return Response({
                'status': 'success',
                'certificates': certificates_data,
                'count': len(certificates_data)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

class CourseCatalogAPI(APIView):
    """API pour voir le catalogue de cours"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            courses = VideoCourse.objects.all().select_related('instructor')
            
            courses_data = []
            for course in courses:
                # Vérifier si l'utilisateur est inscrit
                try:
                    enrollment = CourseEnrollment.objects.get(
                        student=request.user,
                        course=course
                    )
                    enrolled = True
                    progress = enrollment.progress_percentage
                    status = enrollment.status
                except CourseEnrollment.DoesNotExist:
                    enrolled = False
                    progress = 0
                    status = 'not_enrolled'
                
                courses_data.append({
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'instructor': course.instructor.email,
                    'level': course.level,
                    'duration_hours': course.duration_hours,
                    'price': float(course.price),
                    'is_free': course.is_free,
                    'thumbnail_url': course.thumbnail_url,
                    'modules_count': course.modules.count(),
                    'enrolled': enrolled,
                    'progress': progress,
                    'status': status
                })
            
            return Response({
                'status': 'success',
                'courses': courses_data,
                'count': len(courses_data)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)