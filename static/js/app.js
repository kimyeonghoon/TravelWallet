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
        $('#logout-btn').on('click', handleLogout);
        
        // Filter and sort event listeners
        $('#apply-filters').on('click', applyFilters);
        $('#clear-filters').on('click', clearFilters);
        
        // Login modal event listeners
        $('#email-form').on('submit', handleLoginRequest);
        $('#login-code-form').on('submit', handleLoginCodeSubmit);
        $('#back-to-step1').on('click', showLoginStep1);
        $('#login-code').on('input', formatLoginCode);
    }
    
    // Handle expense form submission
    function handleExpenseSubmit(e) {
        e.preventDefault();
        
        const amount = parseFloat($('#amount').val());
        const category = $('#category').val();
        const description = $('#description').val();
        const paymentMethod = $('#payment-method').val();
        
        if (!amount || !category) {
            showAlert('금액과 카테고리를 입력해주세요.', 'warning');
            return;
        }
        
        const expenseData = {
            amount: amount,
            category: category,
            description: description || "",
            payment_method: paymentMethod
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
    function loadExpenses(filters = {}) {
        // Build query parameters
        const params = new URLSearchParams();
        if (filters.category) params.append('category', filters.category);
        if (filters.payment_method) params.append('payment_method', filters.payment_method);
        if (filters.date_from) params.append('date_from', filters.date_from);
        if (filters.date_to) params.append('date_to', filters.date_to);
        if (filters.sort_by) params.append('sort_by', filters.sort_by);
        if (filters.sort_order) params.append('sort_order', filters.sort_order);
        
        // Add cache busting
        params.append('_t', new Date().getTime());
        
        $.ajax({
            url: '/api/expenses?' + params.toString(),
            method: 'GET',
            success: function(expenses) {
                const expenseList = $('#expense-list');
                
                if (expenses.length === 0) {
                    const message = Object.keys(filters).length > 0 ? 
                        '<p class="text-muted text-center">필터 조건에 맞는 지출 내역이 없습니다.</p>' :
                        '<p class="text-muted text-center">아직 지출 내역이 없습니다.</p>';
                    expenseList.html(message);
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
                                        <i class="fas fa-credit-card me-1"></i>${expense.payment_method || '현금'} • 
                                        <i class="fas fa-clock me-1"></i>${displayTime}
                                    </small>
                                </div>
                                ${window.currentUser ? `
                                <div class="btn-group ms-2">
                                    <button class="btn btn-sm btn-outline-primary edit-expense" data-id="${expense.id}">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger delete-expense" data-id="${expense.id}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                                ` : ''}
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
                                    <label for="edit-payment-method" class="form-label">결제 수단</label>
                                    <select class="form-select" id="edit-payment-method" required>
                                        <option value="현금" ${(expense.payment_method || '현금') === '현금' ? 'selected' : ''}>현금</option>
                                        <option value="체크카드" ${expense.payment_method === '체크카드' ? 'selected' : ''}>체크카드</option>
                                        <option value="신용카드" ${expense.payment_method === '신용카드' ? 'selected' : ''}>신용카드</option>
                                        <option value="교통카드" ${expense.payment_method === '교통카드' ? 'selected' : ''}>교통카드</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-amount" class="form-label">금액 (₩)</label>
                                    <input type="number" class="form-control" id="edit-amount" value="${expense.amount}" required>
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
        const paymentMethod = $('#edit-payment-method').val();
        const date = $('#edit-date').val();
        const time = $('#edit-time').val();
        
        if (amount) updateData.amount = parseFloat(amount);
        if (category) updateData.category = category;
        if (description !== undefined) updateData.description = description;
        if (paymentMethod) updateData.payment_method = paymentMethod;
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
    
    // Handle logout
    function handleLogout(e) {
        e.preventDefault();
        
        if (confirm('로그아웃 하시겠습니까?')) {
            $.ajax({
                url: '/api/auth/logout',
                method: 'POST',
                success: function(response) {
                    showAlert('로그아웃되었습니다.', 'info');
                    setTimeout(() => {
                        window.location.reload(); // Reload main page to show login state
                    }, 1000);
                },
                error: function(xhr, status, error) {
                    console.error('Logout error:', error);
                    // Reload page even if logout API fails to clear state
                    window.location.reload();
                }
            });
        }
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
    
    // Login Modal Functions
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
        
        // Send login request with email
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
        
        // Auto-hide success alerts after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                $('.alert').fadeOut();
            }, 5000);
        }
    }

    // Filter and sort functions
    function applyFilters() {
        const filters = {};
        
        // Get filter values
        const category = $('#filter-category').val();
        const paymentMethod = $('#filter-payment').val();
        const dateFrom = $('#filter-date-from').val();
        const dateTo = $('#filter-date-to').val();
        const sortBy = $('#sort-by').val();
        const sortOrder = $('#sort-order').val();
        
        // Build filters object
        if (category) filters.category = category;
        if (paymentMethod) filters.payment_method = paymentMethod;
        if (dateFrom) filters.date_from = dateFrom;
        if (dateTo) filters.date_to = dateTo;
        if (sortBy) filters.sort_by = sortBy;
        if (sortOrder && sortBy) filters.sort_order = sortOrder;
        
        // Validate date range
        if (dateFrom && dateTo && dateFrom > dateTo) {
            showAlert('시작일이 종료일보다 늦을 수 없습니다.', 'warning');
            return;
        }
        
        // Apply filters
        loadExpenses(filters);
        
        // Show success message if filters are applied
        if (Object.keys(filters).length > 0) {
            showAlert('필터가 적용되었습니다.', 'success');
        }
    }
    
    function clearFilters() {
        // Clear all filter inputs
        $('#filter-category').val('');
        $('#filter-payment').val('');
        $('#filter-date-from').val('');
        $('#filter-date-to').val('');
        $('#sort-by').val('');
        $('#sort-order').val('desc');
        
        // Reload all expenses
        loadExpenses();
        
        showAlert('필터가 초기화되었습니다.', 'info');
    }

    // Handle authentication errors globally
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        if (xhr.status === 401 && !settings.url.includes('/api/auth/')) {
            showAlert('로그인이 필요합니다.', 'warning');
            // Show login modal instead of redirecting
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
            loginModal.show();
        }
    });
});