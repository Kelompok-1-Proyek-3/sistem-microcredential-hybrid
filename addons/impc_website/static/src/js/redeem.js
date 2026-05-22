/** @odoo-module **/

/**
 * IMPC Redeem Code JavaScript
 * Handles real-time voucher code validation via AJAX.
 */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const codeInput = document.getElementById('redeem_code_input');
    const submitBtn = document.getElementById('redeem_submit_btn');
    const feedbackDiv = document.getElementById('redeem_validation_feedback');

    if (!codeInput || !submitBtn || !feedbackDiv) return;

    let debounceTimer = null;

    // === Auto-format code input (add dashes) ===
    codeInput.addEventListener('input', function (e) {
        let value = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '');

        // Auto-format: IMPC-XXXX-XXXX-XXXX
        const parts = value.replace(/-/g, '').replace(/^IMPC/, '');
        let formatted = 'IMPC';

        if (parts.length > 0) {
            formatted += '-' + parts.substring(0, 4);
        }
        if (parts.length > 4) {
            formatted += '-' + parts.substring(4, 8);
        }
        if (parts.length > 8) {
            formatted += '-' + parts.substring(8, 12);
        }

        // Only update if different to avoid cursor jump
        if (e.target.value !== formatted) {
            e.target.value = formatted;
        }

        // Debounced validation
        clearTimeout(debounceTimer);
        if (formatted.length === 19) {
            debounceTimer = setTimeout(function () {
                validateCode(formatted);
            }, 500);
        } else {
            feedbackDiv.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    // === Real-time validation via JSON-RPC ===
    function validateCode(code) {
        feedbackDiv.style.display = 'block';
        feedbackDiv.innerHTML = '<span class="text-muted small"><i class="fa fa-spinner fa-spin me-1"></i>Validating...</span>';

        fetch('/my-learning/redeem/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: { code: code },
            }),
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            const result = data.result;
            if (!result) {
                feedbackDiv.innerHTML = '<span class="text-danger small"><i class="fa fa-exclamation-circle me-1"></i>Unable to validate. Please try again.</span>';
                return;
            }

            if (result.valid) {
                feedbackDiv.innerHTML =
                    '<div class="alert alert-success py-2 px-3 mb-0 small">' +
                    '<i class="fa fa-check-circle me-1"></i>' +
                    '<strong>Valid!</strong> Course: ' + result.course_name +
                    '</div>';
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-secondary');
                submitBtn.classList.add('btn-success');
            } else {
                feedbackDiv.innerHTML =
                    '<div class="alert alert-danger py-2 px-3 mb-0 small">' +
                    '<i class="fa fa-times-circle me-1"></i>' +
                    result.message +
                    '</div>';
                submitBtn.disabled = true;
            }
        })
        .catch(function () {
            feedbackDiv.innerHTML = '<span class="text-warning small"><i class="fa fa-exclamation-triangle me-1"></i>Network error. Submit to validate server-side.</span>';
            submitBtn.disabled = false;
        });
    }
});
