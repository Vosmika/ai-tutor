import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from subjects.models import Subject
from assessments.models import WeakTopic
from .models import LearningPath, Flashcard, DailyQuiz
from .generator import generate_learning_path, generate_flashcards


@login_required
def learning_path(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id, owner=request.user)

    if not subject.has_basic_test_completed:
        messages.warning(request, 'Complete your basic test first to unlock personalised recommendations.')
        return redirect('subjects:detail', pk=subject_id)

    path = LearningPath.objects.filter(user=request.user, subject=subject).first()
    weak_topics = WeakTopic.objects.filter(user=request.user, subject=subject)

    # Regenerate if requested
    if request.method == 'POST' or path is None:
        generate_learning_path(request.user, subject)
        path = LearningPath.objects.filter(user=request.user, subject=subject).first()
        messages.success(request, 'Learning path updated!')

    return render(request, 'learning/learning_path.html', {
        'subject': subject,
        'path': path,
        'weak_topics': weak_topics,
    })


@login_required
def flashcards(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id, owner=request.user)

    if not subject.has_basic_test_completed:
        messages.warning(request, 'Complete your basic test first to unlock flashcards.')
        return redirect('subjects:detail', pk=subject_id)

    cards = Flashcard.objects.filter(user=request.user, subject=subject)

    if not cards.exists():
        generate_flashcards(request.user, subject)
        cards = Flashcard.objects.filter(user=request.user, subject=subject)

    return render(request, 'learning/flashcards.html', {
        'subject': subject,
        'flashcards': cards,
    })


@login_required
def daily_quiz_home(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id, owner=request.user)
    today = datetime.date.today()

    if not subject.has_basic_test_completed:
        return render(request, 'learning/daily_quiz.html', {
            'subject': subject,
            'is_locked': True,
            'lock_reason': 'Complete your basic test to unlock daily quizzes.',
        })

    daily, created = DailyQuiz.objects.get_or_create(
        user=request.user,
        subject=subject,
        scheduled_date=today,
        defaults={'is_locked': False}
    )

    # Generate quiz on demand if not already pre-generated.
    # This only fires once per day — subsequent visits just read from DB.
    if daily.quiz is None:
        from assessments.models import WeakTopic
        from assessments.quiz_generator import generate_quiz
        wt = list(WeakTopic.objects.filter(
            user=request.user, subject=subject
        ).values_list('topic_name', flat=True)[:5])
        difficulty = 'focused on weak areas' if wt else 'mixed'
        quiz = generate_quiz(subject, request.user, quiz_type='daily', num_questions=5, difficulty=difficulty)
        if quiz:
            daily.quiz = quiz
            daily.is_locked = False
            daily.save()

    if daily.is_completed:
        attempt = daily.quiz.attempts.filter(user=request.user).first() if daily.quiz else None
        return render(request, 'learning/daily_quiz.html', {
            'subject': subject,
            'daily': daily,
            'is_completed': True,
            'attempt': attempt,
        })

    return render(request, 'learning/daily_quiz.html', {
        'subject': subject,
        'daily': daily,
        'is_locked': daily.is_locked,
    })
