from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import time
import json
from config.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Diagnose Django cache system and AI matching cache'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Cache System Diagnostics'))
        self.stdout.write('='*60)
        
        # Test basic cache functionality
        self._test_basic_cache()
        
        # Test cache configuration
        self._check_cache_config()
        
        # Test AI matching cache specifically
        self._test_ai_matching_cache()
        
        # Test cache with complex data
        self._test_complex_cache()
        
        # Show cache statistics if available
        self._show_cache_stats()
    
    def _test_basic_cache(self):
        """Test basic cache operations"""
        self.stdout.write('\n🧪 Basic Cache Tests:')
        
        # Test simple string caching
        test_key = 'test_cache_key'
        test_value = 'test_cache_value'
        
        try:
            # Set cache
            cache.set(test_key, test_value, 300)  # 5 minutes
            self.stdout.write(self.style.SUCCESS('✅ Cache SET operation successful'))
            
            # Get cache
            retrieved_value = cache.get(test_key)
            if retrieved_value == test_value:
                self.stdout.write(self.style.SUCCESS('✅ Cache GET operation successful'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Cache GET failed - Expected: {test_value}, Got: {retrieved_value}'))
                return False
            
            # Test cache timeout
            cache.set('timeout_test', 'timeout_value', 1)  # 1 second
            time.sleep(2)
            timeout_value = cache.get('timeout_test')
            if timeout_value is None:
                self.stdout.write(self.style.SUCCESS('✅ Cache timeout working correctly'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Cache timeout might not be working - Got: {timeout_value}'))
            
            # Clean up
            cache.delete(test_key)
            self.stdout.write(self.style.SUCCESS('✅ Cache DELETE operation successful'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Basic cache test failed: {e}'))
            return False
        
        return True
    
    def _check_cache_config(self):
        """Check Django cache configuration"""
        self.stdout.write('\\n⚙️ Cache Configuration:')
        
        # Get cache configuration
        cache_config = getattr(settings, 'CACHES', {})
        default_cache = cache_config.get('default', {})
        
        self.stdout.write(f'   Backend: {default_cache.get("BACKEND", "Not configured")}')
        self.stdout.write(f'   Location: {default_cache.get("LOCATION", "Not configured")}')
        self.stdout.write(f'   Timeout: {default_cache.get("TIMEOUT", "Not configured")}')
        
        # Check if using database cache
        if 'DatabaseCache' in default_cache.get('BACKEND', ''):
            self.stdout.write('   📊 Using Database Cache')
            
            # Check if cache table exists
            try:
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%cache%'")
                tables = cursor.fetchall()
                if tables:
                    self.stdout.write(f'   ✅ Cache tables found: {[t[0] for t in tables]}')
                else:
                    self.stdout.write('   ❌ No cache tables found - run: python manage.py createcachetable')
            except Exception as e:
                self.stdout.write(f'   ⚠️ Could not check cache tables: {e}')
        
        # Test cache key generation
        self.stdout.write('\\n🔑 Cache Key Generation Test:')
        from learner.services.ai_service import AIMatchingService
        
        test_learner_id = "test-learner-123"
        test_tutors_hash = "abc123"
        test_cognitive_hash = "def456"
        
        cache_key = AIMatchingService.generate_cache_key(test_learner_id, test_tutors_hash, test_cognitive_hash)
        self.stdout.write(f'   Generated key: {cache_key}')
        self.stdout.write(f'   Key length: {len(cache_key)} characters')
        
        if len(cache_key) == 16 and cache_key.replace('-', '').isalnum():
            self.stdout.write(self.style.SUCCESS('   ✅ Cache key format looks correct'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠️ Cache key format might have issues'))
    
    def _test_ai_matching_cache(self):
        """Test AI matching specific cache behavior"""
        self.stdout.write('\\n🤖 AI Matching Cache Test:')
        
        # Simulate AI matching cache data
        cache_key = 'match_test_abc123_def456'
        test_ai_result = {
            'matches': [
                {
                    'tutor_id': 'test-tutor-1',
                    'final_score': 85,
                    'reasoning': 'Test reasoning',
                    'subject_explanation': 'Test subject match'
                }
            ],
            'ai_processing_time_ms': 1500,
            'cache_hit': False
        }
        
        try:
            # Test caching AI result
            cache.set(cache_key, test_ai_result, 3600)  # 1 hour like in the code
            self.stdout.write(f'   ✅ AI result cached with key: {cache_key}')
            
            # Test retrieving AI result
            retrieved_result = cache.get(cache_key)
            if retrieved_result:
                if retrieved_result.get('matches') == test_ai_result['matches']:
                    self.stdout.write('   ✅ AI result retrieved successfully')
                else:
                    self.stdout.write('   ❌ AI result data mismatch')
            else:
                self.stdout.write('   ❌ AI result not found in cache')
                return False
            
            # Test cache key collision (different but similar keys)
            similar_key = 'match_test_abc124_def456'  # slightly different
            cache.set(similar_key, {'different': 'data'}, 3600)
            
            # Ensure original key still works
            original_result = cache.get(cache_key)
            if original_result and original_result.get('matches') == test_ai_result['matches']:
                self.stdout.write('   ✅ No cache key collision detected')
            else:
                self.stdout.write('   ❌ Possible cache key collision')
            
            # Clean up
            cache.delete(cache_key)
            cache.delete(similar_key)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ AI matching cache test failed: {e}'))
            return False
        
        return True
    
    def _test_complex_cache(self):
        """Test caching with complex data structures"""
        self.stdout.write('\\n📊 Complex Data Cache Test:')
        
        complex_data = {
            'nested_dict': {
                'key1': 'value1',
                'key2': ['item1', 'item2', 'item3']
            },
            'list_of_dicts': [
                {'id': 1, 'name': 'Test 1'},
                {'id': 2, 'name': 'Test 2'}
            ],
            'json_string': json.dumps({'inner': 'json'}),
            'unicode_text': 'Test with émojis 🚀 and spëcial chars',
            'large_number': 1234567890.123456
        }
        
        try:
            cache.set('complex_test', complex_data, 300)
            retrieved_data = cache.get('complex_test')
            
            if retrieved_data == complex_data:
                self.stdout.write('   ✅ Complex data caching works correctly')
            else:
                self.stdout.write('   ❌ Complex data caching failed - data mismatch')
                self.stdout.write(f'      Original keys: {set(complex_data.keys())}')
                self.stdout.write(f'      Retrieved keys: {set(retrieved_data.keys()) if retrieved_data else "None"}')
            
            cache.delete('complex_test')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Complex data cache test failed: {e}'))
    
    def _show_cache_stats(self):
        """Show cache statistics if available"""
        self.stdout.write('\\n📈 Cache Statistics:')
        
        try:
            # Try to get cache stats (may not be available for all backends)
            cache_backend = cache._cache
            
            if hasattr(cache_backend, 'get_stats'):
                stats = cache_backend.get_stats()
                for key, value in stats.items():
                    self.stdout.write(f'   {key}: {value}')
            else:
                self.stdout.write('   ℹ️ Cache statistics not available for this backend')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️ Could not retrieve cache stats: {e}')
        
        # Manual cache inspection
        self.stdout.write('\\n🔍 Manual Cache Inspection:')
        
        # Try to list some keys (database cache specific)
        try:
            if 'DatabaseCache' in getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', ''):
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM django_cache")
                count = cursor.fetchone()[0]
                self.stdout.write(f'   Total cached items in database: {count}')
                
                if count > 0:
                    cursor.execute("SELECT cache_key, LENGTH(value) as size FROM django_cache ORDER BY cache_key LIMIT 5")
                    recent_keys = cursor.fetchall()
                    self.stdout.write('   Recent cache keys:')
                    for key, size in recent_keys:
                        self.stdout.write(f'     - {key[:50]}... (size: {size} bytes)')
            else:
                self.stdout.write('   ℹ️ Manual inspection not available for this cache backend')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️ Could not inspect cache manually: {e}')
        
        # Show recommendations
        self.stdout.write('\\n💡 Recommendations:')
        
        cache_config = getattr(settings, 'CACHES', {}).get('default', {})
        backend = cache_config.get('BACKEND', '')
        
        if 'DummyCache' in backend:
            self.stdout.write(self.style.WARNING('   ⚠️ Using DummyCache - caching is disabled!'))
            self.stdout.write('   💡 Configure a real cache backend in settings.py')
        elif 'DatabaseCache' in backend:
            self.stdout.write('   ✅ Using DatabaseCache - good for development')
            self.stdout.write('   💡 Consider Redis for production')
        elif 'MemcachedCache' in backend or 'RedisCache' in backend:
            self.stdout.write('   ✅ Using high-performance cache backend')
        else:
            self.stdout.write(f'   ℹ️ Using cache backend: {backend}')
        
        self.stdout.write('\\n🎯 Next Steps:')
        self.stdout.write('1. If basic cache tests pass but AI cache fails, check cache key generation')
        self.stdout.write('2. If using DatabaseCache, ensure: python manage.py createcachetable')
        self.stdout.write('3. Check cache timeout settings (default: 300 seconds)')
        self.stdout.write('4. Monitor cache hit/miss rates in production')
        self.stdout.write('5. Consider cache warming strategies for frequently accessed data')