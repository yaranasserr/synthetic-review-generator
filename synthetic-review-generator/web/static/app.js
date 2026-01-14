const API_BASE = '/api';

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Activate button
    event.target.classList.add('active');
}

// Helper functions
function showResult(elementId, content, type = 'info') {
    const resultBox = document.getElementById(elementId);
    resultBox.style.display = 'block';
    resultBox.className = `result-box ${type}`;
    resultBox.innerHTML = content;
}

function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="loader"></span> Processing...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-text') || 'Submit';
    }
}

// Generate single review
async function generateSingle(forceBad = false) {
    const button = event.target;
    button.setAttribute('data-text', button.innerHTML);
    setButtonLoading(button, true);
    
    try {
        const response = await fetch(`${API_BASE}/generate/single`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ force_bad: forceBad })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const review = data.review;
            const html = `
                <div class="review-display">
                    <h4>${review.title}</h4>
                    <p><strong>Rating:</strong> ${review.rating}/5 ⭐</p>
                    <p><strong>Pros:</strong> ${review.pros}</p>
                    <p><strong>Cons:</strong> ${review.cons}</p>
                    <p class="meta">Model: ${review.model} | Persona: ${review.persona}</p>
                </div>
            `;
            showResult('single-result', html, 'success');
        } else {
            showResult('single-result', `<p>❌ Error: ${data.error}</p>`, 'error');
        }
    } catch (error) {
        showResult('single-result', `<p>❌ Error: ${error.message}</p>`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Generate batch reviews
async function generateReviews() {
    const button = event.target;
    button.setAttribute('data-text', button.innerHTML);
    setButtonLoading(button, true);
    
    const count = parseInt(document.getElementById('review-count').value);
    
    if (count < 1 || count > 100) {
        showResult('generate-result', '<p>❌ Please enter a number between 1 and 100</p>', 'error');
        setButtonLoading(button, false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/generate/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ count })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            const html = `
                <h3>✅ Generation Complete!</h3>
                <div class="quality-scores">
                    <div class="score-card passed">
                        <div class="label">Success</div>
                        <div class="value">${result.success_count}</div>
                    </div>
                    <div class="score-card ${result.skipped_count > 0 ? 'failed' : ''}">
                        <div class="label">Skipped</div>
                        <div class="value">${result.skipped_count}</div>
                    </div>
                </div>
                <h4 style="margin-top: 20px;">Generated Files:</h4>
                <ul>
                    <li><a href="/api/files/${result.clean_path}" download>📄 Clean Reviews</a></li>
                    <li><a href="/api/files/${result.with_models_path}" download>📄 Reviews with Models</a></li>
                    <li><a href="/api/files/${result.csv_log}" download>📊 CSV Log</a></li>
                </ul>
                <p style="margin-top: 15px;"><small>Timestamp: ${result.timestamp}</small></p>
            `;
            showResult('generate-result', html, 'success');
        } else {
            showResult('generate-result', `<p>❌ Error: ${data.error}</p>`, 'error');
        }
    } catch (error) {
        showResult('generate-result', `<p>❌ Error: ${error.message}</p>`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Check quality
async function checkQuality() {
    const button = event.target;
    button.setAttribute('data-text', button.innerHTML);
    setButtonLoading(button, true);
    
    const rating = parseFloat(document.getElementById('check-rating').value);
    const title = document.getElementById('check-title').value;
    const text = document.getElementById('check-text').value;
    const keywords = document.getElementById('check-keywords').value.split(',').map(k => k.trim()).filter(k => k);
    
    if (!title || !text) {
        showResult('quality-result', '<p>❌ Please fill in title and review text</p>', 'error');
        setButtonLoading(button, false);
        return;
    }
    
    const review = {
        rating,
        title,
        review_text: `${title}. ${text}`,
        persona_keywords: keywords
    };
    
    try {
        const response = await fetch(`${API_BASE}/quality-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ review })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const check = data.quality_check;
            
            if (check.passed) {
                const scores = check.scores;
                const html = `
                    <h3>✅ Quality Check Passed!</h3>
                    <div class="quality-scores">
                        <div class="score-card passed">
                            <div class="label">Length</div>
                            <div class="value">${scores.length}</div>
                        </div>
                        <div class="score-card passed">
                            <div class="label">Diversity</div>
                            <div class="value">${scores.diversity.toFixed(2)}</div>
                        </div>
                        <div class="score-card passed">
                            <div class="label">Bias</div>
                            <div class="value">${scores.bias.toFixed(2)}</div>
                        </div>
                        <div class="score-card passed">
                            <div class="label">Realism</div>
                            <div class="value">${scores.realism}</div>
                        </div>
                        <div class="score-card passed">
                            <div class="label">Persona</div>
                            <div class="value">${scores.persona}</div>
                        </div>
                    </div>
                `;
                showResult('quality-result', html, 'success');
            } else {
                const html = `
                    <h3>❌ Quality Check Failed</h3>
                    <p><strong>Failed Metric:</strong> ${check.failed_metric}</p>
                    <p><strong>Score:</strong> ${check.score}</p>
                `;
                showResult('quality-result', html, 'error');
            }
        } else {
            showResult('quality-result', `<p>❌ Error: ${data.error}</p>`, 'error');
        }
    } catch (error) {
        showResult('quality-result', `<p>❌ Error: ${error.message}</p>`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Generate quality report
async function generateQualityReport() {
    const button = event.target;
    button.setAttribute('data-text', button.innerHTML);
    setButtonLoading(button, true);
    
    const csvPath = document.getElementById('csv-path').value;
    const syntheticPath = document.getElementById('synthetic-path').value;
    const realPath = document.getElementById('real-path').value;
    const includeCharts = document.getElementById('include-charts').checked;
    
    if (!csvPath) {
        showResult('report-result', '<p>❌ CSV path is required</p>', 'error');
        setButtonLoading(button, false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/reports/quality`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                csv_path: csvPath,
                synthetic_path: syntheticPath || null,
                real_path: realPath || null,
                include_charts: includeCharts
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const html = `
                <h3>✅ Quality Report Generated!</h3>
                <p><a href="/api/files/${data.report_path}" download>📄 Download Report</a></p>
                <pre>${data.report_text}</pre>
            `;
            showResult('report-result', html, 'success');
        } else {
            showResult('report-result', `<p>❌ Error: ${data.error}</p>`, 'error');
        }
    } catch (error) {
        showResult('report-result', `<p>❌ Error: ${error.message}</p>`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Generate comparison report
async function generateComparisonReport() {
    const button = event.target;
    button.setAttribute('data-text', button.innerHTML);
    setButtonLoading(button, true);
    
    const syntheticPath = document.getElementById('synthetic-path').value;
    const realPath = document.getElementById('real-path').value;
    const includeCharts = document.getElementById('include-charts').checked;
    
    if (!syntheticPath || !realPath) {
        showResult('report-result', '<p>❌ Both synthetic and real paths are required</p>', 'error');
        setButtonLoading(button, false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/reports/comparison`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                real_path: realPath,
                synthetic_path: syntheticPath,
                include_charts: includeCharts
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const html = `
                <h3>✅ Comparison Report Generated!</h3>
                <p><a href="/api/files/${data.report_path}" download>📄 Download Report</a></p>
                <pre>${data.report_text}</pre>
            `;
            showResult('report-result', html, 'success');
        } else {
            showResult('report-result', `<p>❌ Error: ${data.error}</p>`, 'error');
        }
    } catch (error) {
        showResult('report-result', `<p>❌ Error: ${error.message}</p>`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            document.getElementById('status').textContent = 'Ready';
            document.getElementById('status').className = 'status-healthy';
        }
    } catch (error) {
        document.getElementById('status').textContent = 'Error';
        document.getElementById('status').className = 'status-error';
    }
}

// Run health check on page load
checkHealth();