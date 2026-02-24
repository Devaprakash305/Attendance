document.addEventListener('DOMContentLoaded', function() {
    // Initialize the date picker with today's date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date').value = today;

    // Fetch total students from Excel on page load
    fetch('/api/get-total-students')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalStudents').value = data.total;
        })
        .catch(error => {
            console.log('Using default total students count');
        });

    // Form submission handler
    document.getElementById('attendanceForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous messages
        hideMessages();
        
        // Show loading state
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        submitBtn.disabled = true;

        try {
            // Collect form data
            const formData = {
                date: document.getElementById('date').value,
                hour: document.getElementById('hour').value,
                department: document.getElementById('department').value,
                course: document.getElementById('course').value,
                totalStudents: document.getElementById('totalStudents').value,
                absent: document.getElementById('absent').value,
                od: document.getElementById('od').value,
                saveToExcel: true
            };

            // Format date for display (DD.MM.YYYY)
            if (formData.date) {
                const dateObj = new Date(formData.date);
                const formattedDate = dateObj.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                }).replace(/\//g, '.');
                formData.date = formattedDate;
            }

            // Send request to backend
            const response = await fetch('/api/process-attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                // Display the report
                document.getElementById('output').textContent = result.report;
                
                // Update statistics
                document.getElementById('statPresent').textContent = result.present;
                document.getElementById('statAbsent').textContent = result.absent;
                document.getElementById('statOD').textContent = result.od;
                document.getElementById('statPercentage').textContent = result.percentage + '%';
                
                // Show success message if Excel was updated
                if (result.excelUpdated) {
                    showTempMessage('Attendance saved to Excel!', 'success');
                }
                
                // Show warnings if any
                if (result.warnings && result.warnings.length > 0) {
                    showWarning(result.warnings.join('<br>'));
                }
            } else {
                // Show error message
                showError(result.error);
            }
        } catch (error) {
            showError('An error occurred while processing. Please try again.');
            console.error('Error:', error);
        } finally {
            // Restore button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });

    // Download Attendance Excel
    document.getElementById('downloadExcelBtn').addEventListener('click', function() {
        window.location.href = '/api/download-attendance';
    });

    // Copy to clipboard
    document.getElementById('copyBtn').addEventListener('click', function() {
        const output = document.getElementById('output').textContent;
        navigator.clipboard.writeText(output).then(function() {
            showTempMessage('Copied to clipboard!', 'success');
        }).catch(function() {
            showError('Failed to copy to clipboard');
        });
    });

    // Print functionality
    document.getElementById('printBtn').addEventListener('click', function() {
        const output = document.getElementById('output').textContent;
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head>
                <title>Attendance Report</title>
                <style>
                    body { font-family: 'Courier New', monospace; padding: 20px; }
                    pre { white-space: pre-wrap; }
                </style>
            </head>
            <body>
                <pre>${output}</pre>
                <script>window.onload = function() { window.print(); window.close(); }<\/script>
            </body>
            </html>
        `);
        printWindow.document.close();
    });

    // Download as PDF
    document.getElementById('downloadBtn').addEventListener('click', function() {
        const output = document.getElementById('output').textContent;
        const date = document.getElementById('date').value;
        
        const element = document.createElement('div');
        element.innerHTML = `<pre style="font-family: 'Courier New', monospace; padding: 20px;">${output}</pre>`;
        
        const opt = {
            margin: 10,
            filename: `attendance_${date}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        
        html2pdf().set(opt).from(element).save();
    });

    // Theme toggle (Dark/Light mode)
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggle.title = 'Toggle Dark Mode';
    document.body.appendChild(themeToggle);

    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        themeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        
        // Save preference
        localStorage.setItem('darkMode', isDark);
    });

    // Load saved theme preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }

    // Helper functions
    function showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.innerHTML = message;
        errorDiv.classList.remove('d-none');
    }

    function showWarning(message) {
        const warningDiv = document.getElementById('warningMessage');
        warningDiv.innerHTML = message;
        warningDiv.classList.remove('d-none');
    }

    function hideMessages() {
        document.getElementById('errorMessage').classList.add('d-none');
        document.getElementById('warningMessage').classList.add('d-none');
    }

function showTempMessage(message, type) {
        const tempDiv = document.createElement('div');
        tempDiv.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        tempDiv.style.zIndex = '9999';
        tempDiv.style.animation = 'slideIn 0.3s ease, fadeOut 0.3s ease 2.7s';
        tempDiv.textContent = message;
        document.body.appendChild(tempDiv);
        
        setTimeout(() => {
            tempDiv.style.opacity = '0';
            tempDiv.style.transform = 'translateY(-20px)';
            setTimeout(() => tempDiv.remove(), 300);
        }, 3000);
    }
});
