from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from video_app.models import Media, StudentMediaInteraction, Comment


class Command(BaseCommand):
    help = 'Rebuilds media like counts and interaction comment counts from actual data. ' \
           'This fixes discrepancies where interaction rows created by comments were ' \
           'being counted as votes. Safe to run multiple times - operates on all data globally.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--update-comment-counts',
            action='store_true',
            help='Also update StudentMediaInteraction.comment_count fields from actual Comment rows',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update_comment_counts = options['update_comment_counts']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Rebuild media like counts
        self.stdout.write('Rebuilding media like counts...')
        media_updated = 0
        media_total = 0
        
        for media in Media.objects.all():
            media_total += 1
            
            # Count actual likes from interactions
            graph_likes = StudentMediaInteraction.objects.filter(
                media=media,
                liked_graph=True
            ).count()
            
            eye_likes = StudentMediaInteraction.objects.filter(
                media=media,
                liked_eye=True
            ).count()
            
            read_likes = StudentMediaInteraction.objects.filter(
                media=media,
                liked_read=True
            ).count()
            
            # Check if update is needed
            needs_update = (
                media.graph_likes != graph_likes or
                media.eye_likes != eye_likes or
                media.read_likes != read_likes
            )
            
            if needs_update:
                if not dry_run:
                    media.graph_likes = graph_likes
                    media.eye_likes = eye_likes
                    media.read_likes = read_likes
                    media.save(update_fields=['graph_likes', 'eye_likes', 'read_likes'])
                
                media_updated += 1
                self.stdout.write(
                    f'  Media {media.id} ({media.title}): '
                    f'graph={graph_likes} (was {media.graph_likes}), '
                    f'eye={eye_likes} (was {media.eye_likes}), '
                    f'read={read_likes} (was {media.read_likes})'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Media like counts: {media_updated} updated out of {media_total} total'
            )
        )
        
        # Optionally rebuild interaction comment counts
        if update_comment_counts:
            self.stdout.write('\nRebuilding interaction comment counts...')
            interaction_updated = 0
            interaction_total = 0
            
            for interaction in StudentMediaInteraction.objects.all():
                interaction_total += 1
                
                # Count actual comments for this student/media pair
                actual_comment_count = Comment.objects.filter(
                    student=interaction.student,
                    media=interaction.media
                ).count()
                
                # Check if update is needed
                if interaction.comment_count != actual_comment_count:
                    if not dry_run:
                        interaction.comment_count = actual_comment_count
                        interaction.save(update_fields=['comment_count'])
                    
                    interaction_updated += 1
                    self.stdout.write(
                        f'  Interaction {interaction.id} (student={interaction.student.name}, '
                        f'media={interaction.media.title}): '
                        f'{actual_comment_count} (was {interaction.comment_count})'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Interaction comment counts: {interaction_updated} updated out of {interaction_total} total'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\nSkipping interaction comment count updates. '
                    'Use --update-comment-counts to rebuild these as well.'
                )
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN COMPLETE - No changes were saved. Run without --dry-run to apply changes.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nRebuild complete!')
            )

