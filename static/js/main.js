// Main JavaScript file for the College Hall Booking System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert:not(.alert-important)');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(flash);
            bsAlert.close();
        }, 5000);
    });
    
    // Booking form validation
    const bookingForm = document.querySelector('form[action*="booking"]');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(event) {
            const startTime = document.getElementById('start_time').value;
            const endTime = document.getElementById('end_time').value;
            
            if (startTime >= endTime) {
                event.preventDefault();
                alert('End time must be after start time.');
                return false;
            }
            
            // Check if booking is for future date
            const now = new Date();
            const bookingStart = new Date(startTime);
            
            if (bookingStart < now) {
                event.preventDefault();
                alert('Booking must be for a future date and time.');
                return false;
            }
            
            return true;
        });
    }
    
    // Hall type filter on halls page
    const hallTypeButtons = document.querySelectorAll('.btn-group[role="group"] .btn');
    hallTypeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            hallTypeButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
        });
    });
    
    // Dynamic update of end time based on start time
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener('change', function() {
            if (this.value && !endTimeInput.value) {
                // Set end time to 1 hour after start time by default
                const startDate = new Date(this.value);
                startDate.setHours(startDate.getHours() + 1);
                
                // Format the date for datetime-local input
                const endDateFormatted = formatDateForInput(startDate);
                endTimeInput.value = endDateFormatted;
            }
        });
    }
    
    // Helper function to format date for datetime-local input
    function formatDateForInput(date) {
        return date.toISOString().slice(0, 16);
    }
    
    // Admin - Confirm actions
    const dangerButtons = document.querySelectorAll('.btn-danger:not([data-bs-toggle])');
    dangerButtons.forEach(button => {
        if (!button.hasAttribute('onclick')) {
            button.addEventListener('click', function(event) {
                if (!confirm('Are you sure you want to perform this action?')) {
                    event.preventDefault();
                    return false;
                }
                return true;
            });
        }
    });
});
