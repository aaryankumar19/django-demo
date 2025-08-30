document.addEventListener("DOMContentLoaded", function() {
    function updateStockUnit() {
        var unitField = document.getElementById("id_unit");
        var stockField = document.getElementById("id_stock");
        if (!unitField || !stockField) return;

        var unitMap = {
            "g": "Grams",
            "kg": "Kilograms",
            "ml": "Milliliters",
            "ltr": "Liters",
            "pcs": "Pieces"
        };

        var unit = unitField.value;
        var helpText = "Stock in " + (unitMap[unit] || "");

        // Django admin renders help text in <p class="help"> inside the form-row
        var help = stockField.closest(".form-row").querySelector(".help");
        if (help) {
            help.textContent = helpText;
        }
    }

    // Run on page load
    updateStockUnit();

    // Update when unit field changes
    var unitField = document.getElementById("id_unit");
    if (unitField) {
        unitField.addEventListener("change", updateStockUnit);
    }
});