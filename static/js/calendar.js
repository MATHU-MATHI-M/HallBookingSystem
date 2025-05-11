// Calendar initialization and functionality

document.addEventListener('DOMContentLoaded', function() {
    // Check if the calendar element exists
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;
    
    // Initialize FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        themeSystem: 'bootstrap5',
        events: '/api/events',
        eventTimeFormat: {
            hour: 'numeric',
            minute: '2-digit',
            meridiem: 'short'
        },
        eventClick: function(info) {
            showEventDetails(info.event);
        },
        dateClick: function(info) {
            // When clicking on a date, you could pre-fill the booking form
            const hallSelect = document.getElementById('hall_id');
            const startTimeInput = document.getElementById('start_time');
            
            if (startTimeInput) {
                // Set the date portion of the start time input
                const currentTime = new Date();
                const hours = String(currentTime.getHours()).padStart(2, '0');
                const minutes = String(currentTime.getMinutes()).padStart(2, '0');
                startTimeInput.value = `${info.dateStr}T${hours}:${minutes}`;
            }
        }
    });
    
    calendar.render();
    
    // Function to show event details in a modal
    function showEventDetails(event) {
        // Create a modal to show event details
        const title = event.title;
        const start = event.start.toLocaleString();
        const end = event.end ? event.end.toLocaleString() : 'Not specified';
        const hall = event.extendedProps.hall;
        const description = event.extendedProps.description || 'No description available';
        
        // You would typically use a modal component from your framework
        alert(`Event: ${title}\nHall: ${hall}\nStart: ${start}\nEnd: ${end}\nDescription: ${description}`);
    }
    
    // If we're on a page with hall_id select, update the calendar when it changes
    const hallSelect = document.getElementById('hall_id');
    if (hallSelect) {
        hallSelect.addEventListener('change', function() {
            const hallId = this.value;
            if (hallId) {
                calendar.removeAllEventSources();
                calendar.addEventSource(`/api/events?hall_id=${hallId}`);
            } else {
                calendar.removeAllEventSources();
                calendar.addEventSource('/api/events');
            }
        });
    }
});
