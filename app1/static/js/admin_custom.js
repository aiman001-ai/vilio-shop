// static/js/admin_custom.js
(function($) {
    $(function() {
        var hasVariants = $('#id_has_variants');
        function toggleFields() {
            if (hasVariants.is(':checked')) {
                // Agar "Without Color" tick hai (Simple Product)
                $('.field-simple_sizes, .field-simple_stock').show();
                $('#color_variants-group').hide();
            } else {
                // Agar variants hain
                $('.field-simple_sizes, .field-simple_stock').hide();
                $('#color_variants-group').show();
            }
        }
        hasVariants.change(toggleFields);
        toggleFields();
    });
})(django.jQuery);