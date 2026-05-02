// Dashboard App
document.addEventListener('DOMContentLoaded', function() {
    // Active navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Update dashboard data (simulated)
    function updateDashboard() {
        
        // This would typically fetch data from an API
        console.log('Dashboard loaded');
    } 


    updateDashboard();
});
