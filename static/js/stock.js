// Stock page specific JavaScript

let canCheckItems = false;
let currentUserType = null; // Will store if user is mail_user or pass_user

// Initialize stock page
function initializeStockPage(activeCategory, canCheck, userType) {
    // Store whether user can check items
    canCheckItems = canCheck;
    currentUserType = userType;
    
    // Add click handlers for service buttons
    $('.service-btn').on('click', function() {
        $('.service-btn').removeClass('active');
        $(this).addClass('active');
        
        const serviceName = $(this).data('service');
        loadServiceData(serviceName);
    });
    
    // Auto-select first service if available
    if (activeCategory) {
        const firstServiceBtn = $('.service-btn').first();
        if (firstServiceBtn.length) {
            firstServiceBtn.addClass('active');
            const serviceName = firstServiceBtn.data('service');
            loadServiceData(serviceName);
        }
    }
    
    // Search functionality
    $('#tableSearch').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        $("#tableBody tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
}

// Load service data
function loadServiceData(serviceName) {
    // First load the price list for this service
    loadPriceList(serviceName);
    
    // Then set up the stock type buttons based on service
    setupStockButtons(serviceName);
    
    // Default to loading "new" type stock for most services
    if (serviceName.toLowerCase() === 'gmail' || 
        serviceName.toLowerCase() === 'outlook') {
        loadStockItems(serviceName, 'one time');
    } else if (serviceName.toLowerCase() === 'linkedin') {
        loadStockItems(serviceName, 'one time');
    } else if (serviceName.toLowerCase() === 'webmail' || 
              serviceName.toLowerCase() === 'edu mail') {
        // These services only have one type
        loadStockItems(serviceName, 'all');
    } else {
        // Default to "new" for Facebook
        loadStockItems(serviceName, 'new');
    }
}

// Load price list for a service
function loadPriceList(serviceName) {
    const priceListTable = $('#priceListTable tbody');
    
    // Clear existing price list
    priceListTable.empty();
    
    // Get services for this category
    $.ajax({
        url: `/api/services/${serviceName.toLowerCase()}`,
        method: 'GET',
        success: function(response) {
            if (response.services && response.services.length > 0) {
                response.services.forEach(function(service) {
                    const row = `
                        <tr>
                            <td>${service.name}</td>
                            <td>${service.is_old ? 'Old' : 'New'}</td>
                            <td>${service.rate.toFixed(2)} BDT</td>
                            <td>${service.validity || 'N/A'}</td>
                        </tr>
                    `;
                    priceListTable.append(row);
                });
            } else {
                priceListTable.append(`
                    <tr>
                        <td colspan="4" class="text-center">No pricing information available for ${serviceName}</td>
                    </tr>
                `);
            }
        },
        error: function() {
            // If API fails, display service rates from the database
            $.ajax({
                url: `/stock/${serviceName}/rates`,
                method: 'GET',
                success: function(response) {
                    if (response && response.rates && Array.isArray(response.rates)) {
                        response.rates.forEach(service => {
                        const row = `
                            <tr>
                                <td>${service.name}</td>
                                <td>${service.type || 'Standard'}</td>
                                <td>${service.rate.toFixed(2)} BDT</td>
                                <td>${service.validity || 'N/A'}</td>
                            </tr>
                        `;
                        priceListTable.append(row);
                        });
                    }
                },
                error: function() {
                    // Fallback when no API data available
                    const row = `
                        <tr>
                            <td>${serviceName}</td>
                            <td>Standard</td>
                            <td>Varies</td>
                            <td>Contact Admin</td>
                        </tr>
                    `;
                    priceListTable.append(row);
                }
            });
        }
    });
}

// Set up stock type buttons based on service
function setupStockButtons(serviceName) {
    const buttonContainer = $('#stockTypeButtons');
    buttonContainer.empty();
    
    if (serviceName.toLowerCase() === 'facebook') {
        // Facebook has new and old
        buttonContainer.append(`
            <button class="btn btn-outline-primary stock-type-btn active" onclick="loadStockItems('${serviceName}', 'new')">New</button>
            <button class="btn btn-outline-secondary stock-type-btn" onclick="loadStockItems('${serviceName}', 'old')">Old</button>
        `);
    } else if (serviceName.toLowerCase() === 'gmail' || 
              serviceName.toLowerCase() === 'outlook') {
        // Gmail and Outlook have one time and old
        buttonContainer.append(`
            <button class="btn btn-outline-primary stock-type-btn active" onclick="loadStockItems('${serviceName}', 'one time')">One Time</button>
            <button class="btn btn-outline-secondary stock-type-btn" onclick="loadStockItems('${serviceName}', 'old')">Old</button>
        `);
    } else if (serviceName.toLowerCase() === 'linkedin') {
        // LinkedIn has one time and old
        buttonContainer.append(`
            <button class="btn btn-outline-primary stock-type-btn active" onclick="loadStockItems('${serviceName}', 'one time')">One Time</button>
            <button class="btn btn-outline-secondary stock-type-btn" onclick="loadStockItems('${serviceName}', 'old')">Old</button>
        `);
    } else if (serviceName.toLowerCase() === 'webmail' || 
              serviceName.toLowerCase() === 'edu mail') {
        // These only have one type
        buttonContainer.append(`
            <button class="btn btn-outline-primary stock-type-btn active" onclick="loadStockItems('${serviceName}', 'all')">All</button>
        `);
    } else {
        // Default buttons
        buttonContainer.append(`
            <button class="btn btn-outline-primary stock-type-btn active" onclick="loadStockItems('${serviceName}', 'all')">All Items</button>
        `);
    }
}

// Load stock items
function loadStockItems(serviceName, itemType) {
    // Set active button
    $('.stock-type-btn').removeClass('active');
    $(`.stock-type-btn`).filter(function() {
        return $(this).text().toLowerCase() === itemType.toLowerCase();
    }).addClass('active');
    
    // Set service title
    $('#serviceTitle').text(`${serviceName} Stock (${itemType})`);
    
    // Clear table and show loading
    $('#tableHeaders').empty();
    $('#tableBody').empty();
    $('#loadingIndicator').show();
    $('#noItemsMessage').hide();
    
    // Fetch stock items
    console.log(`Fetching stock items: /stock/${serviceName}/${itemType}`);
    $.ajax({
        url: `/stock/${serviceName}/${itemType}`,
        method: 'GET',
        success: function(response) {
            $('#loadingIndicator').hide();
            
            const items = response.items;
            if (items.length === 0) {
                $('#noItemsMessage').show();
                return;
            }
            
            // Create headers based on service type
            let headers = [];
            
            // Define headers based on service type according to requirements
            if (serviceName.toLowerCase() === 'facebook') {
                if (itemType.toLowerCase() === 'new') {
                    headers = ['SL', 'Name', 'Mail', 'Pass', 'Profile Link', 'Rate', 'Action'];
                } else {
                    headers = ['SL', 'Name', 'Mail', 'Pass', 'Profile Link', '2FA', 'Created Date', 'Rate', 'Action'];
                }
            } else if (serviceName.toLowerCase() === 'gmail' || serviceName.toLowerCase() === 'outlook') {
                if (itemType.toLowerCase() === 'one time') {
                    headers = ['SL', 'Mail', 'Pass', 'Recovery Mail', 'Rate', 'Action'];
                } else {
                    headers = ['SL', 'Mail', 'Pass', 'Recovery Mail', 'Created Date', 'Rate', 'Action'];
                }
            } else if (serviceName.toLowerCase() === 'linkedin') {
                if (itemType.toLowerCase() === 'one time') {
                    headers = ['SL', 'Name', 'Mail', 'Pass', 'Profile Link', 'Rate', 'Action'];
                } else {
                    headers = ['SL', 'Name', 'Mail', 'Pass', 'Profile Link', '2FA', 'Created Date', 'Rate', 'Action'];
                }
            } else if (serviceName.toLowerCase() === 'webmail' || serviceName.toLowerCase() === 'edu mail') {
                headers = ['SL', 'Mail', 'Pass', 'Rate', 'Action'];
            } else {
                // Default headers
                headers = ['SL', 'Details', 'Rate', 'Action'];
            }
            
            // Create header row
            const headerRow = $('#tableHeaders');
            headers.forEach(header => {
                headerRow.append(`<th>${header}</th>`);
            });
            
            // Create table rows
            const tableBody = $('#tableBody');
            items.forEach(item => {
                let row = `<tr class="stock-item ${item.is_checked ? 'checked' : ''}">`;
                
                // SL column
                row += `<td>${item.sl}</td>`;
                
                if (serviceName.toLowerCase() === 'facebook') {
                    // Facebook specific columns
                    // Mail users cannot see data
                    const canSeeData = currentUserType !== 'mail_user';
                    
                    row += `<td>${canSeeData ? (item.name || 'N/A') : '******'}</td>`;
                    
                    // Hide username part of email but show domain
                    let emailDisplay = item.mail;
                    if (emailDisplay && emailDisplay.includes('@')) {
                        const parts = emailDisplay.split('@');
                        emailDisplay = `***@${parts[1]}`;
                    } else {
                        emailDisplay = '******';
                    }
                    row += `<td>${emailDisplay}</td>`;
                    
                    row += `<td>${canSeeData ? '******' : '******'}</td>`; // Password always hidden until checked
                    
                    // Profile link is always shown
                    row += `<td>${item.profile_link ? '<a href="' + item.profile_link + '" target="_blank">View Profile</a>' : 'N/A'}</td>`;
                    
                    if (itemType.toLowerCase() === 'old') {
                        // 2FA - hidden until checked
                        if (!item.is_checked) {
                            row += `<td><span class="badge bg-warning">Hidden - Check to view</span></td>`;
                        } else {
                            row += `<td>${canSeeData ? (item.two_factor || 'N/A') : '******'}</td>`;
                        }
                        row += `<td>${item.created_date || 'N/A'}</td>`;
                    }
                    
                    row += `<td>${item.rate.toFixed(2)} BDT</td>`;
                    
                } else if (serviceName.toLowerCase() === 'gmail' || serviceName.toLowerCase() === 'outlook') {
                    // Gmail/Outlook specific columns
                    // Pass users cannot see data
                    const canSeeData = currentUserType !== 'pass_user';
                    
                    row += `<td>${canSeeData ? (item.mail || 'N/A') : '******'}</td>`;
                    row += `<td>${canSeeData ? '******' : '******'}</td>`; // Password always hidden until checked
                    
                    // Recovery email - hidden until checked
                    if (!item.is_checked) {
                        row += `<td><span class="badge bg-warning">Hidden - Check to view</span></td>`;
                    } else {
                        row += `<td>${canSeeData ? (item.recovery_mail || 'N/A') : '******'}</td>`;
                    }
                    
                    if (itemType.toLowerCase() === 'old') {
                        row += `<td>${item.created_date || 'N/A'}</td>`;
                    }
                    
                    row += `<td>${item.rate.toFixed(2)} BDT</td>`;
                    
                } else if (serviceName.toLowerCase() === 'linkedin') {
                    // LinkedIn specific columns
                    // Mail users cannot see data
                    const canSeeData = currentUserType !== 'mail_user';
                    
                    row += `<td>${canSeeData ? (item.name || 'N/A') : '******'}</td>`;
                    
                    // Hide username part of email but show domain
                    let emailDisplay = item.mail;
                    if (emailDisplay && emailDisplay.includes('@')) {
                        const parts = emailDisplay.split('@');
                        emailDisplay = `***@${parts[1]}`;
                    } else {
                        emailDisplay = '******';
                    }
                    row += `<td>${emailDisplay}</td>`;
                    
                    row += `<td>${canSeeData ? '******' : '******'}</td>`; // Password always hidden until checked
                    
                    // Profile link is always shown
                    row += `<td>${item.profile_link ? '<a href="' + item.profile_link + '" target="_blank">View Profile</a>' : 'N/A'}</td>`;
                    
                    if (itemType.toLowerCase() === 'old') {
                        // 2FA - hidden until checked
                        if (!item.is_checked) {
                            row += `<td><span class="badge bg-warning">Hidden - Check to view</span></td>`;
                        } else {
                            row += `<td>${canSeeData ? (item.two_factor || 'N/A') : '******'}</td>`;
                        }
                        row += `<td>${item.created_date || 'N/A'}</td>`;
                    }
                    
                    row += `<td>${item.rate.toFixed(2)} BDT</td>`;
                    
                } else if (serviceName.toLowerCase() === 'webmail' || serviceName.toLowerCase() === 'edu mail') {
                    // Webmail/Edu Mail specific columns
                    // Show only domain part of email to users
                    let emailDisplay = item.mail;
                    if (emailDisplay && emailDisplay.includes('@')) {
                        const parts = emailDisplay.split('@');
                        emailDisplay = `***@${parts[1]}`;
                    }
                    
                    row += `<td>${emailDisplay || 'N/A'}</td>`;
                    
                    // Password - hidden until checked
                    if (!item.is_checked) {
                        row += `<td><span class="badge bg-warning">Hidden - Check to view</span></td>`;
                    } else {
                        row += `<td>******</td>`;
                    }
                    
                    row += `<td>${item.rate.toFixed(2)} BDT</td>`;
                } else {
                    // Default columns
                    row += `<td>Item #${item.id}</td>`;
                    row += `<td>${item.rate.toFixed(2)} BDT</td>`;
                }
                
                // Action column
                row += `<td>
                    <button class="btn btn-sm ${item.is_checked ? 'btn-secondary' : 'btn-success'} check-btn" 
                            data-item-id="${item.id}" 
                            ${item.is_checked || !canCheckItems ? 'disabled' : ''}>
                        <i class="fas ${item.is_checked ? 'fa-lock' : 'fa-check'}"></i> 
                        ${item.is_checked ? 'Checked' : 'Check'}
                    </button>
                </td>`;
                
                row += `</tr>`;
                tableBody.append(row);
            });
            
            // Add check button handlers
            $('.check-btn').on('click', function() {
                const itemId = $(this).data('item-id');
                checkStockItem(itemId, serviceName);
            });
        },
        error: function(xhr) {
            $('#loadingIndicator').hide();
            
            if (xhr.status === 403) {
                // Permission error
                $('#noItemsMessage').text('You do not have permission to view this service.').show();
            } else {
                // Other error
                $('#noItemsMessage').text('Error loading stock items. Please try again.').show();
            }
        }
    });
}

// Check a stock item
function checkStockItem(itemId, serviceName) {
    if (!canCheckItems) {
        alert('You need to add funds to check stock items.');
        return;
    }
    
    // Check the item
    $.ajax({
        url: `/stock/check/${itemId}`,
        method: 'POST',
        success: function(response) {
            if (response.success) {
                // Find the row and update it
                const row = $(`.check-btn[data-item-id="${itemId}"]`).closest('tr');
                row.addClass('checked check-animation');
                
                // Update button
                $(`.check-btn[data-item-id="${itemId}"]`)
                    .removeClass('btn-success')
                    .addClass('btn-secondary')
                    .html('<i class="fas fa-lock"></i> Checked')
                    .prop('disabled', true);
                
                // Show item details
                showItemDetails(response.item, serviceName);
                
                // Update balance display
                updateBalance(response.item.rate);
            }
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || 'Error checking item. Please try again.';
            alert(errorMsg);
        }
    });
}

// Show item details in modal
function showItemDetails(item, serviceName) {
    // Set modal title
    $('#itemDetailsModalLabel').text(`${serviceName} Item Details`);
    
    // Create details HTML
    let detailsHtml = `
    <div class="alert alert-success">
        <i class="fas fa-check-circle me-2"></i>Item checked successfully! Here are the complete details:
    </div>
    <div class="container">
    `;
    
    // Add appropriate fields based on service
    if (serviceName.toLowerCase() === 'facebook' || serviceName.toLowerCase() === 'linkedin') {
        detailsHtml += `
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Name:</div>
            <div class="col-md-9">${item.name || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Email:</div>
            <div class="col-md-9">${item.mail || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Password:</div>
            <div class="col-md-9">${item.pass || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Profile Link:</div>
            <div class="col-md-9">
                ${item.profile_link ? 
                    `<a href="${item.profile_link}" target="_blank">${item.profile_link}</a>` : 
                    'N/A'}
            </div>
        </div>
        ${item.two_factor ? `
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">2FA:</div>
            <div class="col-md-9">${item.two_factor}</div>
        </div>
        ` : ''}
        `;
    } else if (serviceName.toLowerCase() === 'gmail' || serviceName.toLowerCase() === 'outlook') {
        detailsHtml += `
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Email:</div>
            <div class="col-md-9">${item.mail || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Password:</div>
            <div class="col-md-9">${item.pass || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Recovery Email:</div>
            <div class="col-md-9">${item.recovery_mail || 'N/A'}</div>
        </div>
        `;
    } else if (serviceName.toLowerCase() === 'webmail' || serviceName.toLowerCase() === 'edu mail') {
        detailsHtml += `
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Email:</div>
            <div class="col-md-9">${item.mail || 'N/A'}</div>
        </div>
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Password:</div>
            <div class="col-md-9">${item.pass || 'N/A'}</div>
        </div>
        `;
    }
    
    // Add common fields
    detailsHtml += `
    <div class="row mb-3">
        <div class="col-md-3 fw-bold">Rate:</div>
        <div class="col-md-9">${item.rate.toFixed(2)} BDT</div>
    </div>
    `;
    
    if (item.created_date) {
        detailsHtml += `
        <div class="row mb-3">
            <div class="col-md-3 fw-bold">Created Date:</div>
            <div class="col-md-9">${item.created_date}</div>
        </div>
        `;
    }
    
    detailsHtml += `
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>This item has been added to your Accounts section. You can find it there at any time.
            </div>
        </div>
    </div>
    </div>
    `;
    
    // Set modal body content
    $('#itemDetailsBody').html(detailsHtml);
    
    // Show the modal
    $('#itemDetailsModal').modal('show');
}

// Update balance display after checking an item
function updateBalance(itemRate) {
    // Get current balance element
    const balanceEl = $('#stockBalance');
    if (balanceEl.length) {
        // Parse current balance
        const currentBalance = parseFloat(balanceEl.text().replace('Balance: ', '').replace(' BDT', ''));
        
        // Calculate new balance
        const newBalance = (currentBalance - itemRate).toFixed(2);
        
        // Update display
        balanceEl.text(`Balance: ${newBalance} BDT`);
    }
}
