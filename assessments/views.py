import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from subjects.models import Subject
from .models import Quiz, Question, QuizAttempt, WeakTopic
from .quiz_generator import generate_quiz

# ❌ ML completely removed
# from ml_engine.predictor import predict_level


@login_required
def start_basic_quiz(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id, owner=request.user)

    existing = Quiz.objects.filter(
        subject=subject, user=request.user, quiz_type='basic', is_completed=False
    ).first()

    if existing:
        return redirect('assessments:take_quiz', quiz_id=existing.pk)

    quiz = generate_quiz(subject, request.user, quiz_type='basic', num_questions=10)
    if quiz is None:
        messages.error(request, 'Failed to generate quiz. Please check your Gemini API key.')
        return redirect('subjects:detail', pk=subject_id)

    return redirect('assessments:take_quiz', quiz_id=quiz.pk)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, user=request.user)

    if quiz.is_completed:
        attempt = quiz.attempts.filter(user=request.user).first()
        if attempt:
            return redirect('assessments:quiz_results', attempt_id=attempt.pk)

    questions = quiz.questions.all()

    return render(request, 'assessments/take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
    })


@login_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('dashboard:home')

    quiz = get_object_or_404(Quiz, pk=quiz_id, user=request.user)
    questions = quiz.questions.all()

    answers = {}
    score = 0
    wrong_topics = []

    for question in questions:
        selected = request.POST.get(f'q_{question.pk}', '').lower()
        answers[str(question.pk)] = selected

        if selected == question.correct_answer:
            score += 1
        else:
            if question.topic_tag:
                wrong_topics.append(question.topic_tag)

    total = questions.count()
    percentage = (score / total * 100) if total > 0 else 0

    # ✅ ML REMOVED → simple logic instead
    if percentage >= 80:
        skill_level = "advanced"
    elif percentage >= 50:
        skill_level = "intermediate"
    else:
        skill_level = "beginner"

    # Update user skill level
    request.user.skill_level = skill_level
    request.user.save(update_fields=['skill_level'])

    # Save attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total_questions=total,
        percentage=round(percentage, 1),
        skill_level=skill_level,
        answers=answers,
    )

    # Mark quiz as completed
    quiz.is_completed = True
    quiz.save()

    # Update weak topics
    for topic in set(wrong_topics):
        obj, created = WeakTopic.objects.get_or_create(
            user=request.user,
            subject=quiz.subject,
            topic_name=topic
        )
        if not created:
            obj.miss_count += 1
            obj.save()

    # Adaptive learning (safe block)
    try:
        from learning.models import Flashcard
        Flashcard.objects.filter(user=request.user, subject=quiz.subject).delete()

        from learning.generator import generate_learning_path
        generate_learning_path(request.user, quiz.subject)
    except Exception as e:
        print(f"Learning content generation error: {e}")

    return redirect('assessments:quiz_results', attempt_id=attempt.pk)


@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    questions = attempt.quiz.questions.all()
    weak_topics = WeakTopic.objects.filter(user=request.user, subject=attempt.quiz.subject)

    question_results = []
    for q in questions:
        selected = attempt.answers.get(str(q.pk), '')
        question_results.append({
            'question': q,
            'selected': selected,
            'is_correct': selected == q.correct_answer,
            'options': q.get_options(),
        })

    return render(request, 'assessments/quiz_results.html', {
        'attempt': attempt,
        'question_results': question_results,
        'weak_topics': weak_topics,
    })


@login_required
def quiz_history(request):
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz__subject')
    return render(request, 'assessments/quiz_history.html', {'attempts': attempts})