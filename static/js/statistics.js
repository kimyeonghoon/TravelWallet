$(document).ready(function() {
    // Initialize statistics dashboard
    loadStatistics();
    
    function loadStatistics() {
        $.ajax({
            url: '/api/statistics',
            method: 'GET',
            success: function(data) {
                console.log('Statistics data:', data);
                populateSummaryCards(data);
                createCharts(data);
                populateTopExpenses(data.top_expenses);
                
                // Hide loading and show content
                $('#loading-state').hide();
                $('#statistics-content').show();
            },
            error: function(xhr, status, error) {
                console.error('Error loading statistics:', error);
                $('#loading-state').html(`
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                        <p class="text-danger">통계 데이터를 불러올 수 없습니다.</p>
                        <button class="btn btn-primary" onclick="location.reload()">다시 시도</button>
                    </div>
                `);
            }
        });
    }
    
    function populateSummaryCards(data) {
        $('#total-amount').text(`₩${data.total_amount.toLocaleString()}`);
        $('#expense-count').text(`${data.expense_count}건`);
        $('#avg-daily').text(`₩${data.avg_daily.toLocaleString()}`);
        $('#total-days').text(`${data.total_days}일`);
    }
    
    function createCharts(data) {
        createCategoryChart(data.category_stats);
        createPaymentChart(data.payment_method_stats);
        createExpenseCalendar(data.daily_stats);
        createWeeklyChart(data.weekly_stats);
    }
    
    function createCategoryChart(categoryStats) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        const categories = Object.keys(categoryStats);
        const amounts = categories.map(cat => categoryStats[cat].amount);
        
        const categoryNames = {
            'food': '식비',
            'transport': '교통비',
            'accommodation': '숙박비',
            'admission': '입장료',
            'other': '기타'
        };
        
        const labels = categories.map(cat => categoryNames[cat] || cat);
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: amounts,
                    backgroundColor: colors.slice(0, categories.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ₩${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function createPaymentChart(paymentStats) {
        const ctx = document.getElementById('paymentChart').getContext('2d');
        
        const methods = Object.keys(paymentStats);
        const amounts = methods.map(method => paymentStats[method].amount);
        
        const colors = ['#FF9F40', '#FF6384', '#4BC0C0', '#36A2EB'];
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: methods,
                datasets: [{
                    data: amounts,
                    backgroundColor: colors.slice(0, methods.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ₩${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // 달력형 지출 조회 기능
    let currentDate = new Date();
    let expenseData = {};

    function createExpenseCalendar(dailyStats) {
        // 일별 통계 데이터를 객체로 변환
        expenseData = {};
        dailyStats.forEach(item => {
            expenseData[item.date] = item.amount;
        });

        // 현재 날짜를 오늘로 설정
        currentDate = new Date();

        renderCalendar();
        bindCalendarEvents();
    }

    function renderCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        // 월 표시 업데이트
        $('#currentMonth').text(`${year}년 ${month + 1}월`);

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const calendarHtml = generateCalendarHTML(year, month, startDate, lastDay);
        $('#calendarContainer').html(calendarHtml);
    }

    function generateCalendarHTML(year, month, startDate, lastDay) {
        let html = '<div class="calendar-grid">';

        // 요일 헤더
        const dayHeaders = ['일', '월', '화', '수', '목', '금', '토'];
        dayHeaders.forEach(day => {
            html += `<div class="calendar-header">${day}</div>`;
        });

        const currentDate = new Date(startDate);
        const today = new Date();

        for (let week = 0; week < 6; week++) {
            for (let day = 0; day < 7; day++) {
                const dateStr = currentDate.toISOString().split('T')[0];
                const dayNum = currentDate.getDate();
                const isCurrentMonth = currentDate.getMonth() === month;
                const isToday = currentDate.toDateString() === today.toDateString();
                const hasExpense = expenseData[dateStr];

                let classes = ['calendar-day'];
                if (!isCurrentMonth) classes.push('other-month');
                if (isToday) classes.push('today');
                if (hasExpense) classes.push('has-expense');

                html += `<div class="${classes.join(' ')}" data-date="${dateStr}">`;
                html += `<div class="day-number">${dayNum}</div>`;
                if (hasExpense && isCurrentMonth) {
                    html += `<div class="day-expense">₩${hasExpense.toLocaleString()}</div>`;
                }
                html += '</div>';

                currentDate.setDate(currentDate.getDate() + 1);
            }
        }

        html += '</div>';
        return html;
    }

    function bindCalendarEvents() {
        $('#prevMonth').off('click').on('click', function() {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
        });

        $('#nextMonth').off('click').on('click', function() {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
        });

        // 달력 셀 클릭 이벤트 (향후 확장 가능)
        $(document).off('click', '.calendar-day').on('click', '.calendar-day', function() {
            const date = $(this).data('date');
            if (expenseData[date]) {
                // 해당 날짜의 지출 상세 정보 표시 (향후 구현)
                console.log(`${date}: ₩${expenseData[date].toLocaleString()}`);
            }
        });
    }
    
    function createWeeklyChart(weeklyStats) {
        const ctx = document.getElementById('weeklyChart').getContext('2d');
        
        // Order by day of week
        const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const dayNames = ['월', '화', '수', '목', '금', '토', '일'];
        
        const orderedData = dayOrder.map(day => weeklyStats[day] || 0);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dayNames,
                datasets: [{
                    label: '요일별 지출',
                    data: orderedData,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                        '#9966FF', '#FF9F40', '#FF6384'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₩' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `지출: ₩${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function populateTopExpenses(topExpenses) {
        const container = $('#top-expenses-list');
        
        if (!topExpenses || topExpenses.length === 0) {
            container.html('<p class="text-muted text-center">지출 데이터가 없습니다.</p>');
            return;
        }
        
        const categoryNames = {
            'food': '식비',
            'transport': '교통비',
            'accommodation': '숙박비',
            'admission': '입장료',
            'other': '기타'
        };
        
        const categoryColors = {
            'food': 'success',
            'transport': 'primary',
            'accommodation': 'secondary',
            'admission': 'warning',
            'other': 'info'
        };
        
        let html = '';
        topExpenses.slice(0, 5).forEach((expense, index) => {
            const categoryName = categoryNames[expense.category] || expense.category;
            const badgeColor = categoryColors[expense.category] || 'secondary';
            
            html += `
                <div class="d-flex justify-content-between align-items-center mb-3 p-3 bg-light rounded">
                    <div>
                        <div class="d-flex align-items-center mb-1">
                            <span class="badge bg-${badgeColor} me-2">${index + 1}</span>
                            <strong class="me-2">₩${expense.amount.toLocaleString()}</strong>
                            <span class="badge bg-outline-${badgeColor}">${categoryName}</span>
                        </div>
                        <small class="text-muted">
                            ${expense.description} • ${expense.payment_method} • ${expense.date}
                        </small>
                    </div>
                </div>
            `;
        });
        
        container.html(html);
    }
    
    // Handle logout
    $('#logout-btn').on('click', function(e) {
        e.preventDefault();
        if (confirm('로그아웃 하시겠습니까?')) {
            $.ajax({
                url: '/api/auth/logout',
                method: 'POST',
                success: function() {
                    window.location.href = '/';
                },
                error: function() {
                    window.location.href = '/';
                }
            });
        }
    });
    
    // Login modal functionality
    $('#email-form').on('submit', handleLoginRequest);
    $('#login-code-form').on('submit', handleLoginCodeSubmit);
    $('#back-to-step1').on('click', showLoginStep1);
    $('#login-code').on('input', formatLoginCode);
    
    function handleLoginRequest(e) {
        e.preventDefault();
        
        const email = $('#login-email').val().trim();
        
        if (!email) {
            showLoginAlert('이메일 주소를 입력해주세요.', 'warning');
            return;
        }
        
        const submitBtn = $('#request-login-btn');
        const btnText = $('#request-btn-text');
        const originalText = btnText.text();
        
        submitBtn.prop('disabled', true);
        btnText.html('<span class="spinner-border spinner-border-sm me-2"></span>전송 중...');
        
        $.ajax({
            url: '/api/auth/login',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                email: email
            }),
            success: function(response) {
                showLoginAlert(response.message, 'success');
                showLoginStep2();
            },
            error: function(xhr, status, error) {
                console.error('Login request failed:', error);
                let errorMessage = '로그인 요청 중 오류가 발생했습니다.';
                
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    errorMessage = xhr.responseJSON.detail;
                }
                
                showLoginAlert(errorMessage, 'danger');
                btnText.text(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    }
    
    function handleLoginCodeSubmit(e) {
        e.preventDefault();
        
        const code = $('#login-code').val().trim();
        
        if (!code || code.length !== 6) {
            showLoginAlert('6자리 코드를 입력해주세요.', 'warning');
            return;
        }
        
        const submitBtn = $('#login-code-form button[type="submit"]');
        const btnText = $('#verify-btn-text');
        const originalText = btnText.text();
        
        submitBtn.prop('disabled', true);
        btnText.html('<span class="spinner-border spinner-border-sm me-2"></span>확인 중...');
        
        $.ajax({
            url: '/api/auth/verify',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                code: code
            }),
            success: function(response) {
                showLoginAlert('로그인 성공! 페이지를 새로고침합니다.', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            },
            error: function(xhr, status, error) {
                console.error('Code verification failed:', error);
                let errorMessage = '코드 확인 중 오류가 발생했습니다.';
                
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    errorMessage = xhr.responseJSON.detail;
                }
                
                showLoginAlert(errorMessage, 'danger');
                btnText.text(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    }
    
    function showLoginStep1() {
        $('#login-step1').show();
        $('#login-step2').hide();
        $('#request-login-btn').prop('disabled', false);
        $('#request-btn-text').text('로그인 코드 받기');
        $('#login-code').val('');
        $('#login-email').val('');
    }
    
    function showLoginStep2() {
        $('#login-step1').hide();
        $('#login-step2').show();
        $('#login-code').focus();
    }
    
    function formatLoginCode() {
        let value = $(this).val().replace(/\D/g, '');
        $(this).val(value);
    }
    
    function showLoginAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('#login-alerts').html(alertHtml);
        
        if (type === 'success') {
            setTimeout(() => {
                $('.alert').fadeOut();
            }, 5000);
        }
    }
});

// Export functionality - global functions
window.exportData = function(format) {
    const url = `/api/export/${format}`;
    
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success message
    showExportAlert(`${format.toUpperCase()} 파일 다운로드가 시작됩니다.`, 'success');
};

window.exportFilteredData = function() {
    const category = $('#export-category').val();
    const paymentMethod = $('#export-payment-method').val();
    const dateFrom = $('#export-date-from').val();
    const dateTo = $('#export-date-to').val();
    const format = $('input[name="export-format"]:checked').val();
    
    // Validate date range
    if (dateFrom && dateTo && dateFrom > dateTo) {
        showExportAlert('시작 날짜는 종료 날짜보다 이전이어야 합니다.', 'warning');
        return;
    }
    
    // Build query parameters
    let params = new URLSearchParams();
    if (category) params.append('category', category);
    if (paymentMethod) params.append('payment_method', paymentMethod);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const url = `/api/export/${format}${params.toString() ? '?' + params.toString() : ''}`;
    
    // Show loading state
    const exportBtn = $('#export-btn-text');
    exportBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>생성 중...');
    $('.btn-success').prop('disabled', true);
    
    // Create and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Reset button state
    setTimeout(() => {
        exportBtn.html('<i class="fas fa-download me-2"></i>내보내기');
        $('.btn-success').prop('disabled', false);
        
        // Show success message
        showExportAlert(`필터가 적용된 ${format.toUpperCase()} 파일 다운로드가 시작됩니다.`, 'success');
        
        // Close modal after success
        setTimeout(() => {
            $('#exportFilterModal').modal('hide');
            window.resetExportForm();
        }, 1500);
    }, 1000);
};

window.showExportAlert = function(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#export-alerts').html(alertHtml);
    
    // Auto-hide success messages
    if (type === 'success') {
        setTimeout(() => {
            $('#export-alerts .alert').fadeOut();
        }, 3000);
    }
};

window.resetExportForm = function() {
    $('#export-filter-form')[0].reset();
    $('#export-alerts').empty();
    $('#format-csv').prop('checked', true);
};

// Reset form when modal is hidden
$('#exportFilterModal').on('hidden.bs.modal', function() {
    window.resetExportForm();
});