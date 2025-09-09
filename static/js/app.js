$(document).ready(function() {
    // Initialize the app
    initApp();
    
    function initApp() {
        loadExpenses();
        updateSummary();
        
        // Event listeners
        $('#expense-form').on('submit', handleExpenseSubmit);
        $(document).on('click', '.delete-expense', handleExpenseDelete);
        $(document).on('click', '.edit-expense', handleExpenseEdit);
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
            url: '/api/expenses?' + new Date().getTime(), // Cache busting
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
                                        <span class="badge bg-primary">₩${expense.amount.toLocaleString()}</span>
                                    </div>
                                    <p class="mb-1 text-muted">${expense.description || '설명 없음'}</p>
                                    <small class="text-muted">
                                        <i class="fas fa-clock me-1"></i>${displayTime}
                                    </small>
                                </div>
                                <div class="btn-group ms-2">
                                    <button class="btn btn-sm btn-outline-primary edit-expense" data-id="${expense.id}">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger delete-expense" data-id="${expense.id}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
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
            url: '/api/summary?' + new Date().getTime(), // Cache busting
            method: 'GET',
            success: function(summary) {
                $('#total-expense').text(`₩${summary.total_expense.toLocaleString()}`);
                $('#today-expense').text(`₩${summary.today_expense.toLocaleString()}`);
            },
            error: function(xhr, status, error) {
                console.error('Error loading summary:', error);
            }
        });
    }
    
    // Handle expense edit
    function handleExpenseEdit(e) {
        const expenseId = parseInt($(this).data('id'));
        
        // Get current expense data
        $.ajax({
            url: `/api/expenses`,
            method: 'GET',
            success: function(expenses) {
                const expense = expenses.find(e => e.id === expenseId);
                if (expense) {
                    showEditModal(expense);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching expense:', error);
                showAlert('지출 정보를 불러올 수 없습니다.', 'danger');
            }
        });
    }
    
    // Show edit modal
    function showEditModal(expense) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="editExpenseModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">지출 수정</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="edit-expense-form">
                                <div class="mb-3">
                                    <label for="edit-amount" class="form-label">금액 (₩)</label>
                                    <input type="number" class="form-control" id="edit-amount" value="${expense.amount}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-category" class="form-label">카테고리</label>
                                    <select class="form-select" id="edit-category" required>
                                        <option value="food" ${expense.category === 'food' ? 'selected' : ''}>식비</option>
                                        <option value="transport" ${expense.category === 'transport' ? 'selected' : ''}>교통비</option>
                                        <option value="accommodation" ${expense.category === 'accommodation' ? 'selected' : ''}>숙박비</option>
                                        <option value="admission" ${expense.category === 'admission' ? 'selected' : ''}>입장료</option>
                                        <option value="other" ${expense.category === 'other' ? 'selected' : ''}>기타</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-description" class="form-label">설명</label>
                                    <input type="text" class="form-control" id="edit-description" value="${expense.description}">
                                </div>
                                <div class="mb-3">
                                    <label for="edit-date" class="form-label">날짜</label>
                                    <input type="date" class="form-control" id="edit-date" value="${expense.date}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-time" class="form-label">시간</label>
                                    <input type="time" class="form-control" id="edit-time" value="${formatTimeFromTimestamp(expense.timestamp)}">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                            <button type="button" class="btn btn-primary" id="save-expense-btn" data-id="${expense.id}">저장</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        $('#editExpenseModal').remove();
        
        // Add modal to body
        $('body').append(modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editExpenseModal'));
        modal.show();
        
        // Handle save button click
        $('#save-expense-btn').on('click', function() {
            const expenseId = parseInt($(this).data('id'));
            updateExpense(expenseId, modal);
        });
    }
    
    // Update expense
    function updateExpense(expenseId, modal) {
        const updateData = {};
        
        // Only include fields that have values
        const amount = $('#edit-amount').val();
        const category = $('#edit-category').val();
        const description = $('#edit-description').val();
        const date = $('#edit-date').val();
        const time = $('#edit-time').val();
        
        if (amount) updateData.amount = parseFloat(amount);
        if (category) updateData.category = category;
        if (description !== undefined) updateData.description = description;
        if (date) updateData.date = date;
        if (time) updateData.time = time;
        
        console.log('Updating expense with data:', updateData);
        
        $.ajax({
            url: `/api/expenses/${expenseId}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(updateData),
            success: function(response) {
                console.log('Update response:', response);
                modal.hide();
                loadExpenses();
                updateSummary();
                showAlert('지출이 수정되었습니다.', 'success');
            },
            error: function(xhr, status, error) {
                console.error('Error updating expense:', error);
                showAlert('지출 수정 중 오류가 발생했습니다.', 'danger');
            }
        });
    }
    
    // Get category name in Korean
    function getCategoryName(category) {
        const categories = {
            food: '식비',
            transport: '교통비',
            accommodation: '숙박비',
            admission: '입장료',
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
    
    // Extract time from timestamp for time input field
    function formatTimeFromTimestamp(timestamp) {
        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
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