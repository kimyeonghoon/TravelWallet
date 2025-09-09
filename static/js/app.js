$(document).ready(function() {
    // Initialize the app
    initApp();
    
    function initApp() {
        loadExpenses();
        updateSummary();
        
        // Event listeners
        $('#expense-form').on('submit', handleExpenseSubmit);
        $(document).on('click', '.delete-expense', handleExpenseDelete);
    }
    
    // Handle expense form submission
    function handleExpenseSubmit(e) {
        e.preventDefault();
        
        const amount = parseFloat($('#amount').val());
        const category = $('#category').val();
        const description = $('#description').val();
        
        if (!amount || !category) {
            showAlert('금액과 카테고리를 입력해주세요.', 'warning');
            return;
        }
        
        const expenseData = {
            amount: amount,
            category: category,
            description: description || ""
        };
        
        // Show loading state
        const submitBtn = $('#expense-form button[type="submit"]');
        const originalText = submitBtn.html();
        submitBtn.html('<span class="loading"></span> 추가 중...').prop('disabled', true);
        
        // Send to API
        $.ajax({
            url: '/api/expenses',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(expenseData),
            success: function(response) {
                $('#expense-form')[0].reset();
                loadExpenses();
                updateSummary();
                showAlert('지출이 추가되었습니다.', 'success');
            },
            error: function(xhr, status, error) {
                console.error('Error adding expense:', error);
                showAlert('지출 추가 중 오류가 발생했습니다.', 'danger');
            },
            complete: function() {
                submitBtn.html(originalText).prop('disabled', false);
            }
        });
    }
    
    // Load and display expenses from API
    function loadExpenses() {
        $.ajax({
            url: '/api/expenses',
            method: 'GET',
            success: function(expenses) {
                const expenseList = $('#expense-list');
                
                if (expenses.length === 0) {
                    expenseList.html('<p class="text-muted text-center">아직 지출 내역이 없습니다.</p>');
                    return;
                }
                
                let html = '';
                expenses.forEach(expense => {
                    // Format timestamp for display
                    const displayTime = formatTimestamp(expense.timestamp);
                    
                    html += `
                        <div class="expense-item category-${expense.category}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <h6 class="mb-0">${getCategoryName(expense.category)}</h6>
                                        <span class="badge bg-primary">¥${expense.amount.toLocaleString()}</span>
                                    </div>
                                    <p class="mb-1 text-muted">${expense.description || '설명 없음'}</p>
                                    <small class="text-muted">
                                        <i class="fas fa-clock me-1"></i>${displayTime}
                                    </small>
                                </div>
                                <button class="btn btn-sm btn-outline-danger delete-expense ms-2" data-id="${expense.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `;
                });
                
                expenseList.html(html);
            },
            error: function(xhr, status, error) {
                console.error('Error loading expenses:', error);
                $('#expense-list').html('<p class="text-danger text-center">지출 내역을 불러올 수 없습니다.</p>');
            }
        });
    }
    
    // Delete expense
    function handleExpenseDelete(e) {
        const expenseId = parseInt($(this).data('id'));
        
        if (confirm('이 지출을 삭제하시겠습니까?')) {
            $.ajax({
                url: `/api/expenses/${expenseId}`,
                method: 'DELETE',
                success: function(response) {
                    loadExpenses();
                    updateSummary();
                    showAlert('지출이 삭제되었습니다.', 'info');
                },
                error: function(xhr, status, error) {
                    console.error('Error deleting expense:', error);
                    showAlert('지출 삭제 중 오류가 발생했습니다.', 'danger');
                }
            });
        }
    }
    
    // Update summary cards from API
    function updateSummary() {
        $.ajax({
            url: '/api/summary',
            method: 'GET',
            success: function(summary) {
                $('#total-budget').text(`¥${summary.total_budget.toLocaleString()}`);
                $('#total-expense').text(`¥${summary.total_expense.toLocaleString()}`);
                $('#remaining-budget').text(`¥${summary.remaining_budget.toLocaleString()}`);
                $('#today-expense').text(`¥${summary.today_expense.toLocaleString()}`);
                
                // Update remaining budget card color
                const remainingCard = $('#remaining-budget').closest('.card');
                if (summary.remaining_budget < 0) {
                    remainingCard.removeClass('bg-info bg-warning').addClass('bg-danger');
                } else if (summary.remaining_budget < summary.total_budget * 0.2) {
                    remainingCard.removeClass('bg-info bg-danger').addClass('bg-warning');
                } else {
                    remainingCard.removeClass('bg-danger bg-warning').addClass('bg-info');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error loading summary:', error);
            }
        });
    }
    
    // Get category name in Korean
    function getCategoryName(category) {
        const categories = {
            food: '식비',
            transport: '교통비',
            accommodation: '숙박비',
            shopping: '쇼핑',
            entertainment: '오락',
            other: '기타'
        };
        return categories[category] || category;
    }
    
    // Format timestamp for display
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Show alert message
    function showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Remove existing alerts
        $('.alert').remove();
        
        // Add new alert at the top of container
        $('.container').prepend(alertHtml);
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            $('.alert').fadeOut();
        }, 3000);
    }
});