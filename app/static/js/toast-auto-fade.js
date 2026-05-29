/**
 * Auto-fades and removes notifications (.notice and .alert) after a delay.
 */
document.addEventListener('DOMContentLoaded', () => {
  const notifications = document.querySelectorAll('.notice, .alert');

  notifications.forEach((notification) => {
    // Add a base transition style
    notification.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    
    // Set timeout to start fading
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateY(-10px)';
      
      // Remove from DOM after transition completes
      setTimeout(() => {
        notification.remove();
      }, 500);
    }, 2000); // 2 seconds delay
  });
});
