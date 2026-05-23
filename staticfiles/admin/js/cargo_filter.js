(function($) {
    $(document).ready(function() {
        var userSelect = $('#id_user'); // Foydalanuvchi tanlash maydoni
        var cargoSelect = $('#id_selected_cargos_from'); // filter_horizontal chap tomoni

        userSelect.on('change', function() {
            var userId = $(this).val();
            if (!userId) return;

            $.getJSON('/admin/get-user-cargos/', {user_id: userId}, function(data) {
                cargoSelect.empty(); // Eskilarini o'chirish
                $.each(data, function(index, item) {
                    cargoSelect.append(
                        $('<option>', { value: item.id, text: item.track_code + " - Yo'lda" })
                    );
                });

                // Django vidjetini yangilab qo'yish (SelectBox yangilanishi uchun)
                if (window.SelectBox) {
                    SelectBox.init('id_selected_cargos_from');
                }
            });
        });
    });
})(django.jQuery);