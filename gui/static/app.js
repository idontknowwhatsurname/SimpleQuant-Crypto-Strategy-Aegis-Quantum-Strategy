/**
 * AIQuant - GUI 交互逻辑
 */

// Tab 切换
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // 移除所有 active
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        // 添加 active
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.getElementById(tabId).classList.add('active');
    });
});

// API 调用封装
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (data) options.body = JSON.stringify(data);
    
    const response = await fetch(url, options);
    return response.json();
}

// 更新状态
async function updateStatus() {
    try {
        const result = await apiCall('/api/status');
        const statusBadge = document.getElementById('engineStatus');
        const statusText = statusBadge.querySelector('.status-text');
        
        if (result.status === 'running') {
            statusBadge.classList.add('running');
            statusText.textContent = '运行中';
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        } else {
            statusBadge.classList.remove('running');
            statusText.textContent = '已停止';
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }
        
        document.getElementById('tradeCount').textContent = result.trade_count || 0;
        document.getElementById('evolutionCount').textContent = result.evolution_count || 0;
        document.getElementById('lastUpdate').textContent = `最后更新: ${new Date().toLocaleTimeString()}`;
    } catch (e) {
        console.error('更新状态失败:', e);
    }
}

// 启动引擎
document.getElementById('startBtn').addEventListener('click', async () => {
    const result = await apiCall('/api/start', 'POST');
    if (result.success) {
        updateStatus();
        alert('引擎已启动');
    }
});

// 停止引擎
document.getElementById('stopBtn').addEventListener('click', async () => {
    const result = await apiCall('/api/stop', 'POST');
    if (result.success) {
        updateStatus();
        alert('引擎已停止');
    }
});

// 运行回测
document.getElementById('runBacktest').addEventListener('click', async () => {
    const resultBox = document.getElementById('backtestResult');
    resultBox.innerHTML = '<div class="loading">回测运行中...</div>';
    
    const result = await apiCall('/api/backtest', 'POST');
    if (result.success) {
        const m = result.metrics;
        resultBox.innerHTML = `
📊 回测结果
━━━━━━━━━━━━━━━━━━━━━━━━
总收益率:     ${m.total_return.toFixed(2)}%
夏普比:       ${m.sharpe.toFixed(2)}
最大回撤:     ${m.max_drawdown.toFixed(2)}%
交易次数:     ${m.trade_count}
━━━━━━━━━━━━━━━━━━━━━━━━
        `;
    } else {
        resultBox.innerHTML = `<div class="loading">❌ 回测失败: ${result.error}</div>`;
    }
});

// 运行复盘
document.getElementById('runReview').addEventListener('click', async () => {
    const resultBox = document.getElementById('reviewResult');
    resultBox.innerHTML = '<div class="loading">复盘分析中...</div>';
    
    const result = await apiCall('/api/review');
    if (result.success) {
        resultBox.textContent = result.report;
    } else {
        resultBox.innerHTML = `<div class="loading">❌ 复盘失败: ${result.error}</div>`;
    }
});

// 手动进化
document.getElementById('runEvolve').addEventListener('click', async () => {
    const resultBox = document.getElementById('evolveResult');
    resultBox.innerHTML = '<div class="loading">策略进化中...</div>';
    
    const result = await apiCall('/api/evolve', 'POST');
    if (result.success) {
        resultBox.textContent = result.report;
    } else {
        resultBox.innerHTML = `<div class="loading">❌ 进化失败: ${result.error}</div>`;
    }
});

// MCP 提示栏
document.getElementById('sendPrompt').addEventListener('click', async () => {
    const prompt = document.getElementById('mcpPrompt').value;
    const model = document.getElementById('modelSelect').value;
    const resultBox = document.getElementById('mcpResponse');
    
    if (!prompt.trim()) {
        alert('请输入提示词');
        return;
    }
    
    resultBox.innerHTML = '<div class="loading">AI 思考中...</div>';
    
    const result = await apiCall('/api/mcp/prompt', 'POST', { prompt, model });
    if (result.success) {
        resultBox.textContent = result.response;
    } else {
        resultBox.innerHTML = `<div class="loading">❌ 请求失败: ${result.error}</div>`;
    }
});

// Goal 任务规划
document.getElementById('executeGoal').addEventListener('click', async () => {
    const goal = document.getElementById('goalInput').value;
    const resultBox = document.getElementById('goalTasks');
    
    if (!goal.trim()) {
        alert('请输入目标');
        return;
    }
    
    resultBox.innerHTML = '<div class="loading">任务规划中...</div>';
    
    const result = await apiCall('/api/goal', 'POST', { goal });
    if (result.success) {
        let html = '<ul class="task-list">';
        result.tasks.forEach(task => {
            html += `
                <li class="task-item">
                    <div class="task-status pending">${task.id}</div>
                    <div class="task-info">
                        <div class="task-name">${task.name}</div>
                        <div class="task-desc">${task.description}</div>
                    </div>
                </li>
            `;
        });
        html += '</ul>';
        resultBox.innerHTML = html;
    } else {
        resultBox.innerHTML = `<div class="loading">❌ 规划失败: ${result.error}</div>`;
    }
});

// 加载持仓
async function loadPortfolio() {
    const result = await apiCall('/api/portfolio');
    const container = document.getElementById('portfolioList');
    
    if (result.success && result.positions.length > 0) {
        let html = '';
        result.positions.forEach(pos => {
            const pnl = parseFloat(pos.unrealizedPnl || 0);
            const pnlClass = pnl >= 0 ? 'success' : 'danger';
            html += `
                <div class="stat">
                    <span class="stat-label">${pos.instId}</span>
                    <span class="stat-value ${pnlClass}">${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}</span>
                </div>
            `;
        });
        container.innerHTML = html;
    } else {
        container.innerHTML = '<div class="loading">无持仓数据</div>';
    }
}

// 初始化
updateStatus();
loadPortfolio();

// 定期刷新状态
setInterval(updateStatus, 30000);
setInterval(loadPortfolio, 60000);
