from django.db import transaction
from ..models import Quiz, QuizAttempt, CourseEnrollment
import random

class QuizService:
    """Service pour gérer les quiz"""
    
    @staticmethod
    def take_quiz(student, quiz_id, answers):
        """Passer un quiz"""
        try:
            with transaction.atomic():
                quiz = Quiz.objects.get(id=quiz_id)
                
                # Trouver l'inscription
                enrollment = CourseEnrollment.objects.get(
                    student=student,
                    course=quiz.module.course
                )
                
                # Vérifier le nombre de tentatives
                attempts_count = QuizAttempt.objects.filter(
                    enrollment=enrollment,
                    quiz=quiz
                ).count()
                
                if attempts_count >= quiz.max_attempts:
                    return {
                        'success': False,
                        'error': f'Nombre maximum de tentatives ({quiz.max_attempts}) atteint'
                    }
                
                # Calculer le score
                score, correct_answers = QuizService._calculate_score(quiz, answers)
                passed = score >= quiz.passing_score
                
                # Sauvegarder la tentative
                attempt = QuizAttempt.objects.create(
                    enrollment=enrollment,
                    quiz=quiz,
                    score=score,
                    passed=passed,
                    answers_data={
                        'answers': answers,
                        'correct_answers': correct_answers,
                        'attempt_number': attempts_count + 1
                    }
                )
                
                return {
                    'success': True,
                    'attempt_id': attempt.id,
                    'score': score,
                    'passed': passed,
                    'passing_score': quiz.passing_score,
                    'attempt_number': attempts_count + 1,
                    'correct_answers': correct_answers,
                    'total_questions': quiz.questions.count()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _calculate_score(quiz, student_answers):
        """Calculer le score d'un quiz"""
        total_questions = quiz.questions.count()
        if total_questions == 0:
            return 0, []
        
        correct_count = 0
        correct_answers = []
        
        for question in quiz.questions.all():
            question_id = str(question.id)
            
            if question_id in student_answers:
                student_answer = student_answers[question_id]
                is_correct = QuizService._check_answer(question, student_answer)
                
                if is_correct:
                    correct_count += 1
                
                correct_answers.append({
                    'question_id': question.id,
                    'question_text': question.text,
                    'student_answer': student_answer,
                    'is_correct': is_correct
                })
        
        score = (correct_count / total_questions) * 100
        return round(score, 2), correct_answers
    
    @staticmethod
    def _check_answer(question, student_answer):
        """Vérifier si une réponse est correcte"""
        if question.question_type == 'multiple_choice':
            # Pour choix multiple, la réponse est l'ID de l'option
            try:
                option_id = int(student_answer)
                correct_option = question.options.get(id=option_id, is_correct=True)
                return True
            except:
                return False
        
        elif question.question_type == 'true_false':
            # Pour vrai/faux, comparer les booléens
            correct_option = question.options.filter(is_correct=True).first()
            if correct_option:
                return str(student_answer).lower() == str(correct_option.text).lower()
        
        elif question.question_type == 'short_answer':
            # Pour réponse courte, vérifier les mots-clés
            correct_options = question.options.filter(is_correct=True)
            student_answer_lower = str(student_answer).lower()
            
            for option in correct_options:
                if option.text.lower() in student_answer_lower:
                    return True
            
            return False
        
        return False
    
    @staticmethod
    def generate_quiz_report(student, course_id):
        """Générer un rapport de quiz pour un cours"""
        try:
            enrollment = CourseEnrollment.objects.get(
                student=student,
                course_id=course_id
            )
            
            quiz_attempts = QuizAttempt.objects.filter(
                enrollment=enrollment
            ).select_related('quiz')
            
            report = {
                'course_id': course_id,
                'course_title': enrollment.course.title,
                'total_quizzes': enrollment.course.modules.filter(quizzes__isnull=False).count(),
                'attempts': []
            }
            
            for attempt in quiz_attempts:
                report['attempts'].append({
                    'quiz_id': attempt.quiz.id,
                    'quiz_title': attempt.quiz.title,
                    'module_title': attempt.quiz.module.title,
                    'score': attempt.score,
                    'passed': attempt.passed,
                    'attempted_at': attempt.attempted_at,
                    'passing_score': attempt.quiz.passing_score
                })
            
            # Calculer les statistiques
            if quiz_attempts:
                passed_attempts = [a for a in quiz_attempts if a.passed]
                report['stats'] = {
                    'total_attempts': len(quiz_attempts),
                    'passed_attempts': len(passed_attempts),
                    'pass_rate': (len(passed_attempts) / len(quiz_attempts)) * 100 if quiz_attempts else 0,
                    'average_score': sum(a.score for a in quiz_attempts) / len(quiz_attempts)
                }
            
            return {
                'success': True,
                'report': report
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }