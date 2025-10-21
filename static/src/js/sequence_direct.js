// Simple script for sequence buttons
window.addEventListener('DOMContentLoaded', function() {
    console.log("Sequence handler loaded");
    
    // Direct click handlers for move up buttons
    document.querySelectorAll('.move-up').forEach(function(btn) {
        btn.addEventListener('click', function() {
            console.log("Move up clicked");
            var item = this.closest('.sequence-item');
            var prev = item.previousElementSibling;
            
            if (prev && prev.classList.contains('sequence-item')) {
                prev.before(item);
                updateNumbers();
                updateData();
            }
        });
    });
    
    // Direct click handlers for move down buttons
    document.querySelectorAll('.move-down').forEach(function(btn) {
        btn.addEventListener('click', function() {
            console.log("Move down clicked");
            var item = this.closest('.sequence-item');
            var next = item.nextElementSibling;
            
            if (next && next.classList.contains('sequence-item')) {
                next.after(item);
                updateNumbers();
                updateData();
            }
        });
    });
    
    // Direct click handler for randomize button
    document.querySelectorAll('.reset-sequence').forEach(function(btn) {
        btn.addEventListener('click', function() {
            console.log("Randomize clicked");
            randomizeItems();
        });
    });
    
    // Initialize
    randomizeItems();
    
    // Functions
    function randomizeItems() {
        var lists = document.querySelectorAll('.sequence-list');
        lists.forEach(function(list) {
            var items = Array.from(list.querySelectorAll('.sequence-item'));
            for (var i = items.length - 1; i > 0; i--) {
                var j = Math.floor(Math.random() * (i + 1));
                list.appendChild(items[j]);
            }
        });
        updateNumbers();
        updateData();
    }
    
    function updateNumbers() {
        var lists = document.querySelectorAll('.sequence-list');
        lists.forEach(function(list) {
            var items = list.querySelectorAll('.sequence-item');
            items.forEach(function(item, index) {
                var numElement = item.querySelector('.step-number');
                if (numElement) {
                    numElement.textContent = (index + 1);
                }
            });
        });
    }
    
    function updateData() {
        var containers = document.querySelectorAll('.sequence-container');
        containers.forEach(function(container) {
            var items = container.querySelectorAll('.sequence-item');
            var data = [];
            
            items.forEach(function(item, index) {
                var stepId = item.dataset.stepId;
                if (stepId) {
                    data.push({
                        step_id: parseInt(stepId),
                        position: index + 1
                    });
                }
            });
            
            var input = container.querySelector('input[name="sequence_data"]');
            if (input) {
                input.value = JSON.stringify(data);
                console.log("Data updated:", input.value);
            }
        });
    }
    
    // Hide "not yet implemented" message if it exists
    var warnings = document.querySelectorAll('.alert-warning');
    warnings.forEach(function(warning) {
        if (warning.textContent.includes('not yet implemented')) {
            warning.style.display = 'none';
        }
    });
});
