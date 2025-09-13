/**
 * 교통수단 기록 관리 JavaScript
 *
 * 이 파일은 교통수단 기록 페이지의 프론트엔드 로직을 담당합니다.
 *
 * 주요 기능:
 * - 교통수단 기록 CRUD 관리
 * - 필터링 및 정렬 기능
 * - 텔레그램 기반 로그인 시스템
 * - 실시간 데이터 업데이트
 *
 * 기술 스택: jQuery, Bootstrap 5
 * API 통신: RESTful API (JSON)
 */

$(document).ready(function() {
    // ==================== 전역 변수 ====================

    let currentEditingId = null;  // 현재 수정 중인 기록 ID

    // ==================== 애플리케이션 초기화 ====================

    // 페이지 로드 시 앱 초기화
    initTransportationApp();

    function initTransportationApp() {
        // 핵심 데이터 로딩
        loadTransportationRecords();  // 교통수단 기록 로딩
        populateTimeOptions();        // 시간 드롭다운 옵션 생성

        // ==================== 이벤트 리스너 등록 ====================

        // 교통수단 기록 관련 이벤트
        $('#transportation-form').on('submit', handleTransportationSubmit);           // 기록 추가
        $(document).on('click', '.delete-transportation', handleTransportationDelete); // 기록 삭제
        $(document).on('click', '.edit-transportation', handleTransportationEdit);     // 기록 수정
        $('#save-transportation').on('click', handleTransportationSave);              // 수정 저장

        // 인증 관련 이벤트
        $('#logout-btn').on('click', handleLogout);  // 로그아웃
        $('#login-form').on('submit', handleLogin);   // 로그인 요청
        $('#verify-form').on('submit', handleVerify); // 코드 인증
        $('#back-to-email').on('click', backToEmail); // 이메일 재입력

        // 필터 및 정렬 이벤트
        $('#apply-filters').on('click', applyFilters);
        $('#filter-category, #filter-date-from, #filter-date-to, #sort-by, #sort-order').on('change', applyFilters);
    }

    /**
     * 시간과 분 드롭다운 옵션 생성
     */
    function populateTimeOptions() {
        // 시간 드롭다운 (0-23시)
        const hourSelectors = ['#departure-hour', '#arrival-hour', '#edit-departure-hour', '#edit-arrival-hour'];
        hourSelectors.forEach(selector => {
            const selectElement = $(selector);
            if (selectElement.length) {
                for (let hour = 0; hour < 24; hour++) {
                    const hourString = hour.toString().padStart(2, '0');
                    selectElement.append(`<option value="${hourString}">${hourString}시</option>`);
                }
            }
        });

        // 분 드롭다운 (0, 15, 30, 45분)
        const minuteSelectors = ['#departure-minute', '#arrival-minute', '#edit-departure-minute', '#edit-arrival-minute'];
        minuteSelectors.forEach(selector => {
            const selectElement = $(selector);
            if (selectElement.length) {
                for (let minute = 0; minute < 60; minute += 15) {
                    const minuteString = minute.toString().padStart(2, '0');
                    selectElement.append(`<option value="${minuteString}">${minuteString}분</option>`);
                }
            }
        });
    }

    // ==================== 교통수단 기록 관리 함수 ====================

    /**
     * 교통수단 기록 목록 로딩
     */
    function loadTransportationRecords() {
        // 필터 값들 가져오기
        const category = $('#filter-category').val();
        const dateFrom = $('#filter-date-from').val();
        const dateTo = $('#filter-date-to').val();
        const sortBy = $('#sort-by').val();
        const sortOrder = $('#sort-order').val();

        // API 요청 매개변수 구성
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        if (sortBy) params.append('sort_by', sortBy);
        if (sortOrder) params.append('sort_order', sortOrder);

        const url = `/api/transportation${params.toString() ? '?' + params.toString() : ''}`;

        $.get(url)
            .done(function(data) {
                displayTransportationRecords(data);
                updateRecordsCount(data.length);
            })
            .fail(function(xhr) {
                console.error('Failed to load transportation records:', xhr);
                showAlert('교통수단 기록을 불러오는데 실패했습니다.', 'danger');
            });
    }

    /**
     * 교통수단 기록 목록 화면 표시 (지출내역 스타일)
     */
    function displayTransportationRecords(records) {
        const container = $('#transportation-list');
        container.empty();

        if (records.length === 0) {
            container.append(`
                <div class="text-center text-muted py-5">
                    <i class="fas fa-inbox fa-3x mb-3"></i><br>
                    <h5>등록된 교통수단 기록이 없습니다.</h5>
                </div>
            `);
            return;
        }

        records.forEach(function(record) {
            const isLoggedIn = $('nav .dropdown-toggle').length > 0; // 로그인 여부 확인
            const actionButtons = isLoggedIn ? `
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary edit-transportation" data-id="${record.id}" title="수정">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger delete-transportation" data-id="${record.id}" title="삭제">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            ` : '';

            // 제목 형태: 교통수단 - 이용회사 (회사명이 있는 경우)
            const title = record.company ? `${record.category} - ${record.company}` : record.category;

            container.append(`
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <!-- 첫 번째 줄: 교통수단, 이용회사 -->
                                <h6 class="card-title mb-2">
                                    <span class="badge bg-${getCategoryBadgeColor(record.category)} me-2">${record.category}</span>
                                    ${record.company ? `<span class="text-muted">${record.company}</span>` : ''}
                                </h6>

                                <!-- 두 번째 줄: 메모 -->
                                ${record.memo ? `<p class="card-text text-muted mb-2"><i class="fas fa-sticky-note me-1"></i>${record.memo}</p>` : ''}

                                <!-- 세 번째 줄: 이용일, 출발시간, 도착시간 -->
                                <div class="d-flex flex-wrap text-sm text-muted">
                                    <span class="me-3">
                                        <i class="fas fa-calendar me-1"></i>${formatDate(record.date)}
                                    </span>
                                    <span class="me-3">
                                        <i class="fas fa-clock me-1"></i>${record.departure_time} → ${record.arrival_time}
                                    </span>
                                </div>
                            </div>

                            <!-- 관리 버튼 -->
                            ${isLoggedIn ? `<div class="ms-3">${actionButtons}</div>` : ''}
                        </div>
                    </div>
                </div>
            `);
        });
    }

    /**
     * 교통수단 카테고리별 뱃지 색상 반환
     */
    function getCategoryBadgeColor(category) {
        const colors = {
            'JR': 'primary',
            '전철': 'success',
            '버스': 'warning',
            '배': 'info',
            '기타': 'secondary'
        };
        return colors[category] || 'secondary';
    }

    /**
     * 기록 수 업데이트
     */
    function updateRecordsCount(count) {
        $('#records-count').text(`${count}건`);
    }

    /**
     * 교통수단 기록 추가 처리
     */
    function handleTransportationSubmit(e) {
        e.preventDefault();

        // 시간 조합
        const departureHour = $('#departure-hour').val();
        const departureMinute = $('#departure-minute').val();
        const arrivalHour = $('#arrival-hour').val();
        const arrivalMinute = $('#arrival-minute').val();

        // 유효성 검사 - 필수 필드
        if (!$('#category').val() || !departureHour || !departureMinute || !arrivalHour || !arrivalMinute) {
            showAlert('모든 필수 항목을 입력해주세요.', 'warning');
            return;
        }

        // 시간 문자열 생성
        const departureTime = `${departureHour}:${departureMinute}`;
        const arrivalTime = `${arrivalHour}:${arrivalMinute}`;

        const formData = {
            category: $('#category').val(),
            company: $('#company').val(),
            departure_time: departureTime,
            arrival_time: arrivalTime,
            memo: $('#memo').val()
        };

        // 시간 유효성 검사
        if (formData.departure_time >= formData.arrival_time) {
            showAlert('도착시간은 출발시간보다 늦어야 합니다.', 'warning');
            return;
        }

        $.ajax({
            url: '/api/transportation',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            data: JSON.stringify(formData),
            success: function(response) {
                showAlert('교통수단 기록이 추가되었습니다.', 'success');
                $('#transportation-form')[0].reset();
                // 시간 드롭다운 초기화
                $('#departure-hour, #departure-minute, #arrival-hour, #arrival-minute').val('');
                loadTransportationRecords();
            },
            error: function(xhr) {
                if (xhr.status === 401) {
                    showAlert('로그인이 필요합니다.', 'warning');
                } else {
                    showAlert('교통수단 기록 추가에 실패했습니다.', 'danger');
                }
                console.error('Failed to create transportation record:', xhr);
            }
        });
    }

    /**
     * 교통수단 기록 수정 모달 표시
     */
    function handleTransportationEdit() {
        const recordId = $(this).data('id');

        // 현재 기록 데이터 찾기
        $.get(`/api/transportation`)
            .done(function(records) {
                const record = records.find(r => r.id === recordId);
                if (record) {
                    currentEditingId = recordId;

                    // 모달 폼에 데이터 채우기
                    $('#edit-transportation-id').val(record.id);
                    $('#edit-category').val(record.category);
                    $('#edit-company').val(record.company);

                    // 시간 분리하여 설정
                    const [depHour, depMinute] = record.departure_time.split(':');
                    const [arrHour, arrMinute] = record.arrival_time.split(':');
                    $('#edit-departure-hour').val(depHour);
                    $('#edit-departure-minute').val(depMinute);
                    $('#edit-arrival-hour').val(arrHour);
                    $('#edit-arrival-minute').val(arrMinute);

                    $('#edit-memo').val(record.memo);
                    $('#edit-date').val(record.date);

                    // 모달 표시
                    $('#editTransportationModal').modal('show');
                }
            })
            .fail(function() {
                showAlert('기록 정보를 불러오는데 실패했습니다.', 'danger');
            });
    }

    /**
     * 교통수단 기록 수정 저장
     */
    function handleTransportationSave() {
        // 시간 조합
        const departureHour = $('#edit-departure-hour').val();
        const departureMinute = $('#edit-departure-minute').val();
        const arrivalHour = $('#edit-arrival-hour').val();
        const arrivalMinute = $('#edit-arrival-minute').val();

        // 유효성 검사 - 필수 필드
        if (!$('#edit-category').val() || !departureHour || !departureMinute || !arrivalHour || !arrivalMinute) {
            showAlert('모든 필수 항목을 입력해주세요.', 'warning');
            return;
        }

        // 시간 문자열 생성
        const departureTime = `${departureHour}:${departureMinute}`;
        const arrivalTime = `${arrivalHour}:${arrivalMinute}`;

        const updateData = {
            category: $('#edit-category').val(),
            company: $('#edit-company').val(),
            departure_time: departureTime,
            arrival_time: arrivalTime,
            memo: $('#edit-memo').val(),
            date: $('#edit-date').val()
        };

        // 시간 유효성 검사
        if (updateData.departure_time >= updateData.arrival_time) {
            showAlert('도착시간은 출발시간보다 늦어야 합니다.', 'warning');
            return;
        }

        $.ajax({
            url: `/api/transportation/${currentEditingId}`,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            data: JSON.stringify(updateData),
            success: function(response) {
                showAlert('교통수단 기록이 수정되었습니다.', 'success');
                $('#editTransportationModal').modal('hide');
                loadTransportationRecords();
            },
            error: function(xhr) {
                if (xhr.status === 401) {
                    showAlert('로그인이 필요합니다.', 'warning');
                } else {
                    showAlert('교통수단 기록 수정에 실패했습니다.', 'danger');
                }
                console.error('Failed to update transportation record:', xhr);
            }
        });
    }

    /**
     * 교통수단 기록 삭제 처리
     */
    function handleTransportationDelete() {
        const recordId = $(this).data('id');

        if (!confirm('이 교통수단 기록을 삭제하시겠습니까?')) {
            return;
        }

        $.ajax({
            url: `/api/transportation/${recordId}`,
            method: 'DELETE',
            success: function(response) {
                showAlert('교통수단 기록이 삭제되었습니다.', 'success');
                loadTransportationRecords();
            },
            error: function(xhr) {
                if (xhr.status === 401) {
                    showAlert('로그인이 필요합니다.', 'warning');
                } else {
                    showAlert('교통수단 기록 삭제에 실패했습니다.', 'danger');
                }
                console.error('Failed to delete transportation record:', xhr);
            }
        });
    }

    /**
     * 필터 적용
     */
    function applyFilters() {
        loadTransportationRecords();
    }

    // ==================== 인증 관련 함수 ====================

    /**
     * 로그인 처리
     */
    function handleLogin(e) {
        e.preventDefault();

        const email = $('#email').val();

        $.ajax({
            url: '/api/auth/login',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            data: JSON.stringify({ email: email }),
            success: function(response) {
                showAlert(response.message, 'success');
                $('#login-step-1').hide();
                $('#login-step-2').show();
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showAlert(response?.detail || '로그인 요청에 실패했습니다.', 'danger');
            }
        });
    }

    /**
     * 인증 코드 검증 처리
     */
    function handleVerify(e) {
        e.preventDefault();

        const code = $('#login-code').val();

        $.ajax({
            url: '/api/auth/verify',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            data: JSON.stringify({ code: code }),
            success: function(response) {
                showAlert('로그인에 성공했습니다. 페이지를 새로고침합니다.', 'success');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            },
            error: function(xhr) {
                const response = xhr.responseJSON;
                showAlert(response?.detail || '인증에 실패했습니다.', 'danger');
            }
        });
    }

    /**
     * 로그아웃 처리
     */
    function handleLogout(e) {
        e.preventDefault();

        $.ajax({
            url: '/api/auth/logout',
            method: 'POST',
            success: function() {
                showAlert('로그아웃되었습니다. 페이지를 새로고침합니다.', 'success');
                setTimeout(() => {
                    location.reload();
                }, 1500);
            },
            error: function() {
                location.reload(); // 실패해도 새로고침
            }
        });
    }

    /**
     * 이메일 재입력으로 돌아가기
     */
    function backToEmail() {
        $('#login-step-2').hide();
        $('#login-step-1').show();
        $('#login-code').val('');
    }

    // ==================== 유틸리티 함수 ====================

    /**
     * 날짜 포맷팅 (YYYY-MM-DD -> YYYY.MM.DD)
     */
    function formatDate(dateString) {
        return dateString.replace(/-/g, '.');
    }

    /**
     * 알림 메시지 표시
     */
    function showAlert(message, type) {
        // 기존 알림 제거
        $('.alert').remove();

        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show position-fixed"
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        $('body').append(alertHtml);

        // 5초 후 자동 제거
        setTimeout(() => {
            $('.alert').fadeOut();
        }, 5000);
    }
});