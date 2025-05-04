document.addEventListener('DOMContentLoaded', function() {
    // Fetch and populate the list of supported pairs
    fetchSupportedPairs();
    
    // Form submission handler
    document.getElementById('biasForm').addEventListener('submit', function(e) {
        e.preventDefault();
        fetchMarketBias();
    });
    
    // Quick pair selection buttons event delegation
    document.getElementById('popularPairs').addEventListener('click', function(e) {
        if (e.target.classList.contains('pair-btn') || e.target.parentElement.classList.contains('pair-btn')) {
            const button = e.target.classList.contains('pair-btn') ? e.target : e.target.parentElement;
            const symbol = button.dataset.symbol;
            document.getElementById('currencyPairInput').value = symbol;
            fetchMarketBias();
        }
    });
});

/**
 * Fetch the supported currency pairs from the server
 */
function fetchSupportedPairs() {
    fetch('/get_supported_pairs')
        .then(response => response.json())
        .then(data => {
            // Populate the datalist for autocomplete
            const datalist = document.getElementById('pairsList');
            data.forEach(pair => {
                const option = document.createElement('option');
                option.value = pair.symbol;
                option.textContent = `${pair.symbol} - ${pair.name}`;
                datalist.appendChild(option);
            });
            
            // Populate the popular pairs section
            const popularPairsContainer = document.getElementById('popularPairs');
            popularPairsContainer.innerHTML = '';
            
            data.forEach(pair => {
                const col = document.createElement('div');
                col.className = 'col-md-4 col-6 mb-2';
                
                col.innerHTML = `
                    <button class="btn btn-outline-secondary w-100 pair-btn" data-symbol="${pair.symbol}">
                        ${pair.symbol}
                    </button>
                `;
                
                popularPairsContainer.appendChild(col);
            });
        })
        .catch(error => {
            console.error('Error fetching supported pairs:', error);
            document.getElementById('popularPairs').innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load popular pairs. Please type a currency pair directly.
                    </div>
                </div>
            `;
        });
}

/**
 * Fetch market bias data for the selected currency pair
 */
function fetchMarketBias() {
    // Get the currency pair from the input
    const currencyPair = document.getElementById('currencyPairInput').value.trim();
    
    if (!currencyPair) {
        showError('Please enter a currency pair or select one from the list.');
        return;
    }
    
    // Show loading indicator
    document.getElementById('loadingIndicator').classList.remove('d-none');
    document.getElementById('resultContainer').classList.add('d-none');
    document.getElementById('errorContainer').classList.add('d-none');
    
    // Create form data
    const formData = new FormData();
    formData.append('currency_pair', currencyPair);
    
    // Send request to server
    fetch('/get_market_bias', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading indicator
        document.getElementById('loadingIndicator').classList.add('d-none');
        
        if (data.status === 'error') {
            showError(data.message);
            return;
        }
        
        // Update UI with the results
        updateResultUI(data);
    })
    .catch(error => {
        document.getElementById('loadingIndicator').classList.add('d-none');
        showError('An error occurred: ' + error.message);
        console.error('Error fetching market bias:', error);
    });
}

/**
 * Update the UI with the fetched market bias data
 */
function updateResultUI(data) {
    // Show result container
    document.getElementById('resultContainer').classList.remove('d-none');
    
    // Update symbol title
    document.getElementById('symbolTitle').textContent = data.symbol;
    
    // Update bias information
    document.getElementById('biasIcon').textContent = data.icon;
    document.getElementById('biasText').textContent = data.bias;
    
    // Update bias strength indicator
    const strengthElement = document.getElementById('biasStrength');
    let strengthBadgeClass = 'bg-secondary';
    let strengthText = 'Weak';
    
    if (data.strength === 'strong' && data.direction === 'up') {
        strengthBadgeClass = 'bg-success';
        strengthText = 'Strong Strength';
    } else if (data.strength === 'strong' && data.direction === 'down') {
        strengthBadgeClass = 'bg-danger';
        strengthText = 'Strong Strength';
    } else if (data.strength === 'moderate' && data.direction === 'up') {
        strengthBadgeClass = 'bg-info';
        strengthText = 'Moderate Strength';
    } else if (data.strength === 'moderate' && data.direction === 'down') {
        strengthBadgeClass = 'bg-warning';
        strengthText = 'Moderate Strength';
    } else {
        strengthText = 'Weak Strength';
    }
    
    strengthElement.innerHTML = `<span class="badge ${strengthBadgeClass}">${strengthText} (${data.score || 0})</span>`;
    
    // Update TradingView recommendation and timeframe information
    const recommendationElement = document.getElementById('tradingviewRecommendation');
    if (recommendationElement) {
        // For backward compatibility with old API
        if (data.tv_recommendation) {
            recommendationElement.innerHTML = `TradingView: <span>${data.tv_recommendation}</span>`;
        } else if (data.timeframes && data.timeframes.daily && data.timeframes.daily.recommendation) {
            recommendationElement.innerHTML = `TradingView: <span>${data.timeframes.daily.recommendation}</span>`;
        } else {
            recommendationElement.innerHTML = `TradingView: <span>N/A</span>`;
        }
    }
    
    // Update daily and weekly bias information
    const dailyBiasElement = document.getElementById('dailyBias');
    const weeklyBiasElement = document.getElementById('weeklyBias');
    
    if (dailyBiasElement && data.timeframes && data.timeframes.daily) {
        const dailyScore = data.timeframes.daily.score;
        let dailyBiasText = "Sideways";
        
        if (dailyScore >= 50) dailyBiasText = "Strong Bullish";
        else if (dailyScore >= 20) dailyBiasText = "Bullish";
        else if (dailyScore <= -50) dailyBiasText = "Strong Bearish";
        else if (dailyScore <= -20) dailyBiasText = "Bearish";
        
        dailyBiasElement.textContent = `Daily: ${dailyBiasText} (${dailyScore})`;
        
        // Apply color based on score
        dailyBiasElement.className = 'small';
        if (dailyScore >= 40) dailyBiasElement.classList.add('text-success');
        else if (dailyScore <= -40) dailyBiasElement.classList.add('text-danger');
    }
    
    if (weeklyBiasElement && data.timeframes && data.timeframes.weekly) {
        const weeklyScore = data.timeframes.weekly.score;
        let weeklyBiasText = "Sideways";
        
        if (weeklyScore >= 50) weeklyBiasText = "Strong Bullish";
        else if (weeklyScore >= 20) weeklyBiasText = "Bullish";
        else if (weeklyScore <= -50) weeklyBiasText = "Strong Bearish";
        else if (weeklyScore <= -20) weeklyBiasText = "Bearish";
        
        weeklyBiasElement.textContent = `Weekly: ${weeklyBiasText} (${weeklyScore})`;
        weeklyBiasElement.className = 'small';
        
        // Apply color based on score
        if (weeklyScore >= 40) weeklyBiasElement.classList.add('text-success');
        else if (weeklyScore <= -40) weeklyBiasElement.classList.add('text-danger');
        
        // Show the weekly timeframe section
        document.getElementById('timeframeSection').classList.remove('d-none');
    } else if (weeklyBiasElement) {
        // Hide weekly bias if not available
        weeklyBiasElement.parentElement.classList.add('d-none');
    }
    
    // Update technical indicators for advanced users
    const rsiElement = document.getElementById('rsiValue');
    const macdElement = document.getElementById('macdValue');
    const ema20Element = document.getElementById('ema20Value');
    const ema50Element = document.getElementById('ema50Value');
    
    if (rsiElement && data.indicators) {
        rsiElement.textContent = data.indicators.rsi || 'N/A';
        
        // Color RSI based on common overbought/oversold levels
        if (data.indicators.rsi > 70) {
            rsiElement.classList.add('text-danger');
        } else if (data.indicators.rsi < 30) {
            rsiElement.classList.add('text-success');
        } else {
            rsiElement.classList.remove('text-danger', 'text-success');
        }
    }
    
    if (macdElement && data.indicators) {
        const macdValue = data.indicators.macd || 0;
        const signalValue = data.indicators.macd_signal || 0;
        macdElement.textContent = `${macdValue} / ${signalValue}`;
        
        // Color MACD based on crossover (bullish or bearish)
        if (macdValue > signalValue) {
            macdElement.classList.add('text-success');
            macdElement.classList.remove('text-danger');
        } else if (macdValue < signalValue) {
            macdElement.classList.add('text-danger');
            macdElement.classList.remove('text-success');
        } else {
            macdElement.classList.remove('text-danger', 'text-success');
        }
    }
    
    if (ema20Element && data.indicators) {
        ema20Element.textContent = data.indicators.ema20 || 'N/A';
    }
    
    if (ema50Element && data.indicators) {
        ema50Element.textContent = data.indicators.ema50 || 'N/A';
    }
    
    // Update price information
    document.getElementById('prevClose').textContent = data.prev_price;
    document.getElementById('currentClose').textContent = data.current_price;
    
    // Update price change with appropriate color and arrow
    const priceChangeElement = document.getElementById('priceChange');
    let changeHTML = '';
    
    if (data.direction === 'up') {
        changeHTML = `
            <span class="badge bg-success">
                <i class="fas fa-arrow-up me-1"></i>${data.change_percentage}%
            </span>
        `;
    } else if (data.direction === 'down') {
        changeHTML = `
            <span class="badge bg-danger">
                <i class="fas fa-arrow-down me-1"></i>${data.change_percentage}%
            </span>
        `;
    } else {
        changeHTML = `
            <span class="badge bg-secondary">
                <i class="fas fa-minus me-1"></i>${data.change_percentage}%
            </span>
        `;
    }
    
    priceChangeElement.innerHTML = changeHTML;
    
    // Update header background color based on bias
    const headerElement = document.getElementById('resultHeader');
    headerElement.className = 'card-header';
    
    if (data.direction === 'up') {
        headerElement.classList.add('bg-success');
    } else if (data.direction === 'down') {
        headerElement.classList.add('bg-danger');
    } else {
        headerElement.classList.add('bg-secondary');
    }
}

/**
 * Show an error message
 */
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    document.getElementById('errorMessage').textContent = message;
    errorContainer.classList.remove('d-none');
    document.getElementById('resultContainer').classList.add('d-none');
}
