from django.utils import timezone
from django.db import transaction
from ..models import VideoCourse, CourseEnrollment, VideoView, VideoModule
import time
from datetime import timedelta

class VideoTrackingService:
    """Service pour suivre la progression des vidéos"""
    
    @staticmethod
    def track_video_view(student, module_id, watch_duration, total_duration):
        """Suivre la visualisation d'une vidéo"""
        try:
            # Calculer le pourcentage regardé
            watched_percentage = (watch_duration / total_duration * 100) if total_duration > 0 else 0
            
            with transaction.atomic():
                # Trouver ou créer l'inscription
                module = VideoModule.objects.get(id=module_id)
                enrollment, _ = CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=module.course,
                    defaults={'status': 'active'}
                )
                
                # Mettre à jour ou créer la vue
                video_view, created = VideoView.objects.get_or_create(
                    enrollment=enrollment,
                    module=module,
                    defaults={
                        'watch_duration_seconds': watch_duration,
                        'watched_percentage': watched_percentage,
                        'completed': watched_percentage >= 90  # 90% = complété
                    }
                )
                
                if not created:
                    video_view.watch_duration_seconds += watch_duration
                    video_view.watched_percentage = max(video_view.watched_percentage, watched_percentage)
                    video_view.completed = video_view.completed or (watched_percentage >= 90)
                    video_view.save()
                
                # Mettre à jour la progression du cours
                VideoTrackingService._update_course_progress(enrollment)
                
                return {
                    'success': True,
                    'enrollment_id': enrollment.id,
                    'video_view_id': video_view.id,
                    'watched_percentage': watched_percentage,
                    'completed': video_view.completed
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _update_course_progress(enrollment):
        """Mettre à jour la progression globale du cours"""
        total_modules = enrollment.course.modules.count()
        completed_modules = VideoView.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        if total_modules > 0:
            progress = (completed_modules / total_modules) * 100
            enrollment.progress_percentage = progress
            
            # Marquer comme terminé si tous les modules sont complétés
            if completed_modules == total_modules and enrollment.status == 'active':
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
            
            enrollment.save()
    
    @staticmethod
    def get_course_progress(student, course_id):
        """Obtenir la progression d'un étudiant dans un cours"""
        try:
            enrollment = CourseEnrollment.objects.get(
                student=student,
                course_id=course_id
            )
            
            modules = enrollment.course.modules.all()
            module_progress = []
            
            for module in modules:
                try:
                    view = VideoView.objects.get(
                        enrollment=enrollment,
                        module=module
                    )
                    module_progress.append({
                        'module_id': module.id,
                        'title': module.title,
                        'watched_percentage': view.watched_percentage,
                        'completed': view.completed,
                        'last_watched': view.last_watched_at
                    })
                except VideoView.DoesNotExist:
                    module_progress.append({
                        'module_id': module.id,
                        'title': module.title,
                        'watched_percentage': 0,
                        'completed': False,
                        'last_watched': None
                    })
            
            return {
                'success': True,
                'course_id': course_id,
                'course_title': enrollment.course.title,
                'overall_progress': enrollment.progress_percentage,
                'status': enrollment.status,
                'modules': module_progress,
                'enrolled_at': enrollment.enrolled_at,
                'completed_at': enrollment.completed_at
            }
            
        except CourseEnrollment.DoesNotExist:
            return {
                'success': False,
                'error': 'Non inscrit à ce cours'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def is_course_completed(student, course_id):
        """Vérifier si un étudiant a terminé un cours"""
        try:
            enrollment = CourseEnrollment.objects.get(
                student=student,
                course_id=course_id,
                status='completed'
            )
            
            # Vérifier que tous les modules sont complétés
            total_modules = enrollment.course.modules.count()
            completed_modules = VideoView.objects.filter(
                enrollment=enrollment,
                completed=True
            ).count()
            
            return {
                'success': True,
                'completed': completed_modules == total_modules,
                'completion_date': enrollment.completed_at
            }
            
        except CourseEnrollment.DoesNotExist:
            return {
                'success': False,
                'completed': False,
                'error': 'Cours non terminé'
            }