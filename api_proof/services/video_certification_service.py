from django.utils import timezone
from django.db import transaction
from ..models import (
    CourseEnrollment, VideoCourseCertificate, 
     CardanoWallet, QuizAttempt
)
from .video_tracking import VideoTrackingService
import hashlib

class VideoCertificationService:
    
    def __init__(self, network='preprod'):
        self.network = network
    
    def check_eligibility_for_certification(self, student, course_id):
        """Vérifier si un étudiant est éligible à la certification"""
        try:
            enrollment = CourseEnrollment.objects.get(
                student=student,
                course_id=course_id
            )
            
            # 1. Vérifier que le cours est terminé
            progress_result = VideoTrackingService.get_course_progress(student, course_id)
            if not progress_result['success'] or enrollment.status != 'completed':
                return {
                    'eligible': False,
                    'reason': 'Cours non terminé',
                    'progress': progress_result.get('overall_progress', 0)
                }
            
            # 2. Vérifier tous les quiz (doivent être réussis)
            course = enrollment.course
            all_passed = True
            quiz_results = []
            
            for module in course.modules.all():
                for quiz in module.quizzes.all():
                    # Vérifier si au moins une tentative est réussie
                    passed_attempt = QuizAttempt.objects.filter(
                        enrollment=enrollment,
                        quiz=quiz,
                        passed=True
                    ).exists()
                    
                    quiz_results.append({
                        'module': module.title,
                        'quiz': quiz.title,
                        'passed': passed_attempt,
                        'passing_score': quiz.passing_score
                    })
                    
                    if not passed_attempt:
                        all_passed = False
            
            if not all_passed:
                return {
                    'eligible': False,
                    'reason': 'Quiz non réussis',
                    'quiz_results': quiz_results
                }
            
            # 3. Vérifier si déjà certifié
            already_certified = VideoCourseCertificate.objects.filter(
                enrollment=enrollment
            ).exists()
            
            if already_certified:
                return {
                    'eligible': False,
                    'reason': 'Déjà certifié'
                }
            
            # 4. Calculer les compétences vérifiées
            verified_skills = self._extract_verified_skills(course, enrollment)
            
            return {
                'eligible': True,
                'student': student.email,
                'course': course.title,
                'completion_date': enrollment.completed_at,
                'verified_skills': verified_skills,
                'quiz_results': quiz_results
            }
            
        except Exception as e:
            return {
                'eligible': False,
                'reason': f'Erreur: {str(e)}'
            }
    
    def _extract_verified_skills(self, course, enrollment):
        """Extraire les compétences vérifiées durant le cours"""
        skills = []
        
        # Compétences de base du cours
        if 'django' in course.title.lower() or 'python' in course.title.lower():
            skills.append('Python')
            skills.append('Django')
            skills.append('Backend Development')
        
        if 'cardano' in course.title.lower() or 'blockchain' in course.title.lower():
            skills.append('Blockchain')
            skills.append('Cardano')
            skills.append('Smart Contracts')
        
        if 'web' in course.title.lower() or 'frontend' in course.title.lower():
            skills.append('Web Development')
            skills.append('HTML/CSS')
            skills.append('JavaScript')
        
        # Ajouter des compétences basées sur les quiz réussis
        passed_quizzes = QuizAttempt.objects.filter(
            enrollment=enrollment,
            passed=True
        ).select_related('quiz')
        
        for attempt in passed_quizzes:
            if 'api' in attempt.quiz.title.lower():
                skills.append('API Development')
            if 'database' in attempt.quiz.title.lower():
                skills.append('Database Design')
            if 'security' in attempt.quiz.title.lower():
                skills.append('Web Security')
        
        return list(set(skills))  # Éliminer les doublons
    
    def issue_certification_nft(self, student, course_id, issuer_wallet_id=None):
        """Émettre un NFT de certification"""
        try:
            with transaction.atomic():
                # Vérifier l'éligibilité
                eligibility = self.check_eligibility_for_certification(student, course_id)
                
                if not eligibility['eligible']:
                    return {
                        'success': False,
                        'error': f'Non éligible: {eligibility.get("reason", "Raison inconnue")}'
                    }
                
                enrollment = CourseEnrollment.objects.get(
                    student=student,
                    course_id=course_id
                )
                
                course = enrollment.course
                
                # Préparer les données de certification
                certification_data = {
                    'title': f"Certification: {course.title}",
                    'description': f"Certifie la complétion du cours {course.title} avec succès",
                    'type': 'Video Course Completion',
                    'recipient_name': student.get_full_name() or student.email,
                    'recipient_address': self._get_student_wallet_address(student),
                    'issuer_name': course.instructor.get_full_name() or course.instructor.email,
                    'course_id': course.id,
                    'course_title': course.title,
                    'completion_date': enrollment.completed_at.isoformat(),
                    'level': course.level,
                    'duration_hours': course.duration_hours,
                    'verified_skills': eligibility['verified_skills'],
                    'instructor': course.instructor.email,
                    'issue_date': timezone.now().date().isoformat()
                }
                
                # Si pas d'adresse wallet pour l'étudiant, on ne peut pas émettre le NFT
                if not certification_data['recipient_address']:
                    # Créer un certificat sans NFT (en attente)
                    certificate = VideoCourseCertificate.objects.create(
                        enrollment=enrollment,
                        skills_verified=eligibility['verified_skills']
                    )
                    
                    return {
                        'success': True,
                        'certificate_issued': True,
                        'nft_issued': False,
                        'certificate_id': certificate.id,
                        'message': 'Certificat créé sans NFT (adresse wallet manquante)',
                        'certification_data': certification_data
                    }
                
                # Pour l'instant, simulation (vous pouvez intégrer le minting réel ici)
                certificate = VideoCourseCertificate.objects.create(
                    enrollment=enrollment,
                    skills_verified=eligibility['verified_skills']
                )
                
                # Simulation de création NFT
                nft_simulation = self._simulate_nft_creation(certification_data)
                
                return {
                    'success': True,
                    'certificate_issued': True,
                    'nft_issued': True,
                    'certificate_id': certificate.id,
                    'certification_data': certification_data,
                    'nft_simulation': nft_simulation,
                    'note': 'Mode simulation - intégrez le minting réel ici'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_student_wallet_address(self, student):
        """Récupérer l'adresse Cardano d'un étudiant"""
        # Chercher un wallet associé à l'utilisateur
        try:
            wallet = CardanoWallet.objects.filter(user=student).first()
            return wallet.payment_address if wallet else None
        except:
            return None
    
    def _simulate_nft_creation(self, certification_data):
        """Simuler la création d'un NFT (pour développement)"""
        import time
        
        # Générer un fingerprint simulé
        unique_id = f"{certification_data['course_id']}_{certification_data['recipient_name']}_{int(time.time())}"
        fingerprint = f"asset1sim{hashlib.sha256(unique_id.encode()).hexdigest()[:32]}"
        
        return {
            'fingerprint': fingerprint,
            'policy_id': f"policy_sim_{hashlib.sha256(certification_data['course_title'].encode()).hexdigest()[:16]}",
            'asset_name': f"CERT_{certification_data['course_id']}_{int(time.time())}",
            'metadata': certification_data,
            'explorer_url': f"https://{self.network}.cardanoscan.io/search?filter=simulated"
        }
    



from api_proof.models import VideoCourse, VideoModule, User

instructor = User.objects.get(email='test@example.com')
course = VideoCourse.objects.create(
    title="Formation Django & Cardano",
    description="Apprenez à intégrer Django avec Cardano",
    instructor=instructor,
    level='intermediate',
    duration_hours=10,
    is_free=True
)