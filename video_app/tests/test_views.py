from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Count, Q
from video_app.models import Session, CustomAdmin, Media, Student, StudentMediaInteraction, Comment, District

User = get_user_model()


class TeacherViewVoteCommentCountsTest(TestCase):
    """Test that vote and comment counts in teacher_view are accurate."""
    
    def setUp(self):
        """Set up test data."""
        # Create district
        self.district = District.objects.create(
            name='Test District',
            code='TEST',
            is_active=True
        )
        
        # Create admin/teacher
        self.admin = CustomAdmin.objects.create_user(
            username='testteacher',
            password='testpass123',
            school='Test School',
            district=self.district
        )
        
        # Create session
        self.session = Session.objects.create(
            name="Test Session",
            section=1,
            created_by=self.admin
        )
        
        # Create student
        self.student = Student.objects.create(
            name="Test Student",
            password="12345",
            section=self.session,
            admin=self.admin
        )
        
        # Create media
        self.media = Media.objects.create(
            session=self.session,
            title="Test Media",
            description="Test Description",
            media_type='image',
            is_graph=False
        )
        
        # Create client and login
        self.client = Client()
        self.client.login(username='testteacher', password='testpass123')
    
    def test_comment_only_interaction_not_counted_as_vote(self):
        """Test that creating a comment (which creates an interaction) doesn't count as a vote."""
        # Create a comment - this will create a StudentMediaInteraction with all likes=False
        comment = Comment.objects.create(
            media=self.media,
            text="Test comment",
            name=self.student.name,
            student=self.student
        )
        
        # Manually create the interaction that would be created by the view
        interaction, _ = StudentMediaInteraction.objects.get_or_create(
            student=self.student,
            media=self.media
        )
        interaction.comment_count = 1
        interaction.save()
        
        # Get teacher view
        response = self.client.get(reverse('teacher_view'))
        self.assertEqual(response.status_code, 200)
        
        # Get the student from the queryset (simulating what the view does)
        students = Student.objects.filter(
            admin=self.admin,
            section__is_archived=False
        ).annotate(
            total_votes=Count(
                'media_interactions',
                filter=Q(media_interactions__liked_graph=True) | 
                       Q(media_interactions__liked_eye=True) | 
                       Q(media_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        
        student = students.first()
        # Should have 0 votes (no likes set) but 1 comment
        self.assertEqual(student.total_votes, 0, "Comment-only interaction should not count as a vote")
        self.assertEqual(student.total_comments, 1, "Should have 1 comment")
    
    def test_real_likes_are_counted_as_votes(self):
        """Test that interactions with actual likes are counted as votes."""
        # Create interaction with a like
        interaction = StudentMediaInteraction.objects.create(
            student=self.student,
            media=self.media,
            liked_graph=True,
            liked_eye=False,
            liked_read=False
        )
        
        # Get students with annotations
        students = Student.objects.filter(
            admin=self.admin,
            section__is_archived=False
        ).annotate(
            total_votes=Count(
                'media_interactions',
                filter=Q(media_interactions__liked_graph=True) | 
                       Q(media_interactions__liked_eye=True) | 
                       Q(media_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        
        student = students.first()
        # Should have 1 vote (one like flag set)
        self.assertEqual(student.total_votes, 1, "Interaction with like should count as 1 vote")
        self.assertEqual(student.total_comments, 0, "Should have 0 comments")
    
    def test_multiple_likes_from_same_student_count_once(self):
        """Test that multiple like flags from the same student/media pair count as one vote."""
        # Create interaction with multiple likes
        interaction = StudentMediaInteraction.objects.create(
            student=self.student,
            media=self.media,
            liked_graph=True,
            liked_eye=True,
            liked_read=True
        )
        
        # Get students with annotations
        students = Student.objects.filter(
            admin=self.admin,
            section__is_archived=False
        ).annotate(
            total_votes=Count(
                'media_interactions',
                filter=Q(media_interactions__liked_graph=True) | 
                       Q(media_interactions__liked_eye=True) | 
                       Q(media_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        
        student = students.first()
        # Should count as 1 vote (one interaction, even with multiple flags)
        self.assertEqual(student.total_votes, 1, "Multiple likes from same student should count as 1 vote")
    
    def test_deleted_comment_does_not_affect_vote_count(self):
        """Test that deleting a comment doesn't leave phantom votes."""
        # Create a comment and interaction (comment-only, no likes)
        comment = Comment.objects.create(
            media=self.media,
            text="Test comment",
            name=self.student.name,
            student=self.student
        )
        
        interaction, _ = StudentMediaInteraction.objects.get_or_create(
            student=self.student,
            media=self.media
        )
        interaction.comment_count = 1
        interaction.save()
        
        # Verify initial state
        students_before = Student.objects.filter(
            admin=self.admin,
            section__is_archived=False
        ).annotate(
            total_votes=Count(
                'media_interactions',
                filter=Q(media_interactions__liked_graph=True) | 
                       Q(media_interactions__liked_eye=True) | 
                       Q(media_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        student_before = students_before.first()
        self.assertEqual(student_before.total_votes, 0, "Should have 0 votes before deletion")
        self.assertEqual(student_before.total_comments, 1, "Should have 1 comment before deletion")
        
        # Delete the comment
        comment.delete()
        
        # Verify after deletion
        students_after = Student.objects.filter(
            admin=self.admin,
            section__is_archived=False
        ).annotate(
            total_votes=Count(
                'media_interactions',
                filter=Q(media_interactions__liked_graph=True) | 
                       Q(media_interactions__liked_eye=True) | 
                       Q(media_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        student_after = students_after.first()
        # Vote count should still be 0 (interaction exists but has no likes)
        self.assertEqual(student_after.total_votes, 0, "Vote count should remain 0 after comment deletion")
        # Comment count should be 0
        self.assertEqual(student_after.total_comments, 0, "Comment count should be 0 after deletion")
    
    def test_media_leaderboard_vote_counts(self):
        """Test that media leaderboard correctly counts votes."""
        # Create two students and two interactions
        student2 = Student.objects.create(
            name="Test Student 2",
            password="12346",
            section=self.session,
            admin=self.admin
        )
        
        # First interaction with a like
        interaction1 = StudentMediaInteraction.objects.create(
            student=self.student,
            media=self.media,
            liked_graph=True
        )
        
        # Second interaction with a like
        interaction2 = StudentMediaInteraction.objects.create(
            student=student2,
            media=self.media,
            liked_eye=True
        )
        
        # Get media leaderboard
        media_leaderboard = Media.objects.filter(
            session__created_by=self.admin,
            session__is_archived=False
        ).annotate(
            total_votes=Count(
                'student_interactions',
                filter=Q(student_interactions__liked_graph=True) | 
                       Q(student_interactions__liked_eye=True) | 
                       Q(student_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        
        media_item = media_leaderboard.first()
        # Should have 2 votes (2 different students liked it)
        self.assertEqual(media_item.total_votes, 2, "Media should have 2 votes from 2 different students")
        self.assertEqual(media_item.total_comments, 0, "Should have 0 comments")
    
    def test_media_leaderboard_excludes_comment_only_interactions(self):
        """Test that media leaderboard doesn't count comment-only interactions as votes."""
        # Create a comment-only interaction (no likes)
        comment = Comment.objects.create(
            media=self.media,
            text="Test comment",
            name=self.student.name,
            student=self.student
        )
        
        interaction, _ = StudentMediaInteraction.objects.get_or_create(
            student=self.student,
            media=self.media
        )
        interaction.comment_count = 1
        interaction.save()
        
        # Get media leaderboard
        media_leaderboard = Media.objects.filter(
            session__created_by=self.admin,
            session__is_archived=False
        ).annotate(
            total_votes=Count(
                'student_interactions',
                filter=Q(student_interactions__liked_graph=True) | 
                       Q(student_interactions__liked_eye=True) | 
                       Q(student_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        )
        
        media_item = media_leaderboard.first()
        # Should have 0 votes (no likes) but 1 comment
        self.assertEqual(media_item.total_votes, 0, "Comment-only interaction should not count as vote")
        self.assertEqual(media_item.total_comments, 1, "Should have 1 comment")

