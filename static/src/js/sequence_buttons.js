// Very simple sequence button handlers
(function() {
    "use strict";

    // Run when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
    const DEBUG = false; if(DEBUG) console.log('Sequence buttons initialized');
        
        // Setup the buttons
        setupButtons();
        
        // Randomize on first load
        randomizeAllItems();
    });
    
    function setupButtons() {
        // Setup up buttons
        var upButtons = document.querySelectorAll('.move-up');
        for (var i = 0; i < upButtons.length; i++) {
            upButtons[i].addEventListener('click', handleMoveUp);
        }
        
        // Setup down buttons
        var downButtons = document.querySelectorAll('.move-down');
        for (var i = 0; i < downButtons.length; i++) {
            downButtons[i].addEventListener('click', handleMoveDown);
        }
        
        // Setup reset buttons
        var resetButtons = document.querySelectorAll('.reset-sequence');
        for (var i = 0; i < resetButtons.length; i++) {
            resetButtons[i].addEventListener('click', handleReset);
        }
        
        // Hide any "not implemented" messages
        var warnings = document.querySelectorAll('.alert-warning');
        for (var i = 0; i < warnings.length; i++) {
            if (warnings[i].textContent.indexOf('not yet implemented') !== -1) {
                warnings[i].style.display = 'none';
            }
        }
    }
    
    function handleMoveUp(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var item = this.closest('.sequence-item');
        var prev = item.previousElementSibling;
        
        if (prev && prev.classList.contains('sequence-item')) {
            var parent = item.parentNode;
            parent.insertBefore(item, prev);
            updateOrder(item.closest('.sequence-container'));
        }
    }
    
    function handleMoveDown(e) {
        e.preventDefault();
        e.stopPropagation();
        
        var item = this.closest('.sequence-item');
        var next = item.nextElementSibling;
        
        if (next && next.classList.contains('sequence-item')) {
            var parent = item.parentNode;
            parent.insertBefore(next, item);
            updateOrder(item.closest('.sequence-container'));
        }
    }
    
    function handleReset(e) {
        e.preventDefault();
        
        var container = this.closest('.sequence-container');
        randomizeItems(container);
        updateOrder(container);
    }
    
    function randomizeAllItems() {
        var containers = document.querySelectorAll('.sequence-container');
        for (var i = 0; i < containers.length; i++) {
            randomizeItems(containers[i]);
            updateOrder(containers[i]);
        }
    }
    
    function randomizeItems(container) {
        var list = container.querySelector('.sequence-list');
        if (!list) return;
        
        var items = list.querySelectorAll('.sequence-item');
        var itemArray = Array.prototype.slice.call(items);
        
        // Shuffle the array
        for (var i = itemArray.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            list.appendChild(itemArray[j]);
        }
    }
    
    function updateOrder(container) {
        if (!container) return;
        
        // Update numbers
        var items = container.querySelectorAll('.sequence-item');
        for (var i = 0; i < items.length; i++) {
            var numEl = items[i].querySelector('.step-number');
            if (numEl) {
                numEl.textContent = (i + 1);
            }
        }
        
        // Update data
        var data = [];
        for (var i = 0; i < items.length; i++) {
            var stepId = items[i].getAttribute('data-step-id');
            if (stepId) {
                data.push({
                    step_id: parseInt(stepId),
                    position: i + 1
                });
            }
        }
        
        var input = container.querySelector('input[name="sequence_data"]');
        if (input) {
            input.value = JSON.stringify(data);
                if(DEBUG) console.log("Updated sequence data:", input.value);
        }
    }
})();
