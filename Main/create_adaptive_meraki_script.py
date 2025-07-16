#!/usr/bin/env python3
"""
Create an enhanced version of the Meraki script with adaptive rate limiting
that speeds up until hitting limits, then backs off slightly
"""

import os
import shutil

# Read the current script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'r') as f:
    content = f.read()

# Find where to insert the adaptive rate limiter class
import_section_end = content.find('logger = logging.getLogger(__name__)')
if import_section_end == -1:
    import_section_end = content.find('# Configuration constants')

# Create the adaptive rate limiter class
adaptive_rate_limiter = '''
# Adaptive Rate Limiter for Meraki API
class AdaptiveRateLimiter:
    """
    Dynamically adjusts API call speed based on rate limit responses.
    Speeds up until hitting limits, then backs off slightly.
    """
    def __init__(self):
        self.min_delay = 0.05  # 50ms minimum (20 requests/sec theoretical max)
        self.max_delay = 2.0   # 2 seconds maximum
        self.current_delay = 0.5  # Start conservative at 500ms
        self.speed_increase_factor = 0.9  # Reduce delay by 10% when speeding up
        self.speed_decrease_factor = 1.5  # Increase delay by 50% when hitting limits
        self.consecutive_successes = 0
        self.consecutive_429s = 0
        self.requests_made = 0
        self.rate_limits_hit = 0
        self.last_delay_change = time.time()
        self.delay_change_cooldown = 10  # Wait 10 seconds between speed changes
        
    def record_success(self):
        """Record a successful API call"""
        self.requests_made += 1
        self.consecutive_successes += 1
        self.consecutive_429s = 0
        
        # Speed up after 50 consecutive successes
        if self.consecutive_successes >= 50:
            self._try_speed_up()
            
    def record_rate_limit(self):
        """Record hitting a rate limit"""
        self.rate_limits_hit += 1
        self.consecutive_429s += 1
        self.consecutive_successes = 0
        
        # Immediately back off on rate limit
        self._back_off()
        
    def _try_speed_up(self):
        """Try to reduce delay (speed up API calls)"""
        if time.time() - self.last_delay_change < self.delay_change_cooldown:
            return
            
        old_delay = self.current_delay
        self.current_delay = max(self.min_delay, self.current_delay * self.speed_increase_factor)
        if old_delay != self.current_delay:
            logger.info(f"API Rate: Speeding up - delay reduced from {old_delay:.3f}s to {self.current_delay:.3f}s")
            self.last_delay_change = time.time()
            self.consecutive_successes = 0
            
    def _back_off(self):
        """Increase delay (slow down API calls)"""
        old_delay = self.current_delay
        self.current_delay = min(self.max_delay, self.current_delay * self.speed_decrease_factor)
        if old_delay != self.current_delay:
            logger.info(f"API Rate: Backing off - delay increased from {old_delay:.3f}s to {self.current_delay:.3f}s")
            self.last_delay_change = time.time()
            
    def wait(self):
        """Wait for the current delay period"""
        time.sleep(self.current_delay)
        
    def get_stats(self):
        """Get current rate limiter statistics"""
        return {
            'current_delay': self.current_delay,
            'requests_made': self.requests_made,
            'rate_limits_hit': self.rate_limits_hit,
            'effective_rate': 1.0 / self.current_delay if self.current_delay > 0 else 0
        }

# Global rate limiter instance
rate_limiter = AdaptiveRateLimiter()

'''

# Insert the rate limiter after the logger setup
insert_pos = content.find('logger = logging.getLogger(__name__)') + len('logger = logging.getLogger(__name__)\n')
content = content[:insert_pos] + '\n' + adaptive_rate_limiter + content[insert_pos:]

# Replace the make_api_request function with adaptive version
old_function_start = content.find('def make_api_request(url, api_key, params=None, max_retries=5):')
old_function_end = content.find('\n\ndef', old_function_start)

new_make_api_request = '''def make_api_request(url, api_key, params=None, max_retries=5):
    """Make a GET request to the Meraki API with adaptive rate limiting."""
    headers = get_headers(api_key)
    
    for attempt in range(max_retries):
        try:
            # Wait based on adaptive rate limiter
            rate_limiter.wait()
            
            # Log every 100 requests
            if rate_limiter.requests_made % 100 == 0:
                stats = rate_limiter.get_stats()
                logger.info(f"API Performance: {stats['requests_made']} requests, "
                          f"Rate limited: {stats['rate_limits_hit']} times, "
                          f"Current rate: {stats['effective_rate']:.1f} req/sec")
            
            logger.debug(f"Requesting {url}")
            resp = requests.get(url, headers=headers, params=params)
            
            if resp.status_code == 429:  # rate limit
                rate_limiter.record_rate_limit()
                retry_after = int(resp.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retry-After: {retry_after}s. Backing off...")
                time.sleep(min(retry_after, 60))  # Cap at 60 seconds
                continue
                
            resp.raise_for_status()
            rate_limiter.record_success()
            return resp.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                rate_limiter.record_rate_limit()
                continue
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)
    return []'''

content = content[:old_function_start] + new_make_api_request + content[old_function_end:]

# Remove the fixed time.sleep(0.2) after processing each device
content = content.replace('                    time.sleep(0.2)', '                    # Adaptive rate limiting handles delays')

# Remove the fixed time.sleep(1) from the old make_api_request
content = content.replace('            time.sleep(1)  # ensure at most 1 request per second to Meraki', '')

# Also remove time.sleep(0.5) from firewall collection
content = content.replace('            time.sleep(0.5)  # Rate limiting', '            # Adaptive rate limiting handles delays')

# Add performance summary at the end of main()
main_end_marker = '        logger.info(f"Completed inventory. Processed {devices_processed} devices and stored in database")'
performance_summary = '''
        
        # Log final performance statistics
        final_stats = rate_limiter.get_stats()
        logger.info(f"API Performance Summary:")
        logger.info(f"  Total requests: {final_stats['requests_made']}")
        logger.info(f"  Rate limits hit: {final_stats['rate_limits_hit']}")
        logger.info(f"  Final request rate: {final_stats['effective_rate']:.1f} req/sec")
        logger.info(f"  Final delay: {final_stats['current_delay']:.3f}s")
        
        logger.info(f"Completed inventory. Processed {devices_processed} devices and stored in database")'''

content = content.replace(main_end_marker, performance_summary)

# Write the enhanced script
output_path = '/usr/local/bin/Main/nightly_meraki_db_adaptive.py'
with open(output_path, 'w') as f:
    f.write(content)

print(f"Created adaptive rate limiting version at: {output_path}")
print("\nKey features added:")
print("- Starts at 2 requests/second (conservative)")
print("- Speeds up after 50 consecutive successful requests")
print("- Can reach up to 20 requests/second (50ms delay)")
print("- Immediately backs off on rate limit (429) responses")
print("- Respects Retry-After headers from Meraki")
print("- Logs performance statistics every 100 requests")
print("- Final performance summary at end of run")
print("\nThe script will constantly adapt during execution:")
print("- Speeding up when API is responsive")
print("- Backing off when hitting limits")
print("- Finding the optimal speed for current conditions")