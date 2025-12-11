from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.cache import cache
from config.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Setup and test Django cache system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Setting up Django Cache System'))
        self.stdout.write('='*50)
        
        # Create cache table
        self._create_cache_table()
        
        # Test basic cache functionality
        self._test_cache()
        
        # Show next steps
        self._show_next_steps()
    
    def _create_cache_table(self):
        """Create the Django cache table"""
        self.stdout.write('\\n📊 Creating cache table...')
        
        try:
            # Create cache table
            call_command('createcachetable', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Cache table created successfully'))
        except Exception as e:
            if 'already exists' in str(e):
                self.stdout.write(self.style.SUCCESS('✅ Cache table already exists'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create cache table: {e}'))
                return False
        
        return True
    
    def _test_cache(self):
        """Test basic cache operations"""
        self.stdout.write('\\n🧪 Testing cache operations...')
        
        try:
            # Test cache set
            cache.set('setup_test', 'cache_working', 300)
            self.stdout.write('✅ Cache SET successful')
            
            # Test cache get
            value = cache.get('setup_test')
            if value == 'cache_working':
                self.stdout.write('✅ Cache GET successful')
                
                # Test AI matching cache format
                ai_test_data = {
                    'matches': [
                        {'tutor_id': 'test-123', 'final_score': 85}
                    ],
                    'ai_processing_time_ms': 1500,
                    'cache_hit': False
                }
                
                cache.set('ai_match_test', ai_test_data, 3600)
                retrieved = cache.get('ai_match_test')
                
                if retrieved and retrieved['matches'][0]['tutor_id'] == 'test-123':
                    self.stdout.write('✅ AI matching cache format works')
                else:
                    self.stdout.write('❌ AI matching cache format failed')
                
                # Clean up
                cache.delete('setup_test')
                cache.delete('ai_match_test')
                
            else:
                self.stdout.write(f'❌ Cache GET failed - got: {value}')
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cache test failed: {e}'))
            return False
        
        return True
    
    def _show_next_steps(self):
        """Show next steps"""
        self.stdout.write('\\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 Cache setup completed!'))
        
        self.stdout.write('\\n📝 Next steps:')
        self.stdout.write('1. Run: python manage.py diagnose_cache  (for detailed diagnostics)')
        self.stdout.write('2. Test AI matching cache by calling the API twice quickly')
        self.stdout.write('3. Check logs for cache hit messages')
        
        self.stdout.write('\\n🔍 Expected behavior:')
        self.stdout.write('- First API call: "No cached result found" + AI call')
        self.stdout.write('- Second API call: "Cache hit for matching request" + no AI call')
        
        self.stdout.write('\\n⚠️ Cache will be invalidated if:')
        self.stdout.write('- Tutors are added/removed/modified')
        self.stdout.write('- Learner cognitive assessment changes')
        self.stdout.write('- Cache TTL expires (1 hour by default)')