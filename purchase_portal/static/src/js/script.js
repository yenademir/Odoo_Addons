odoo.define('purchase_portal.currency_loader', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function () {
        // Mevcut para birimi ID'sini al
        var currentCurrencyId = $('div[data-current-currency-id]').data('current-currency-id');

        // Sayfa yüklendiğinde para birimlerini al
        ajax.jsonRpc('/get_currencies', 'call', {}).then(function (data) {
            // Para birimleri alındığında select seçeneğini doldur
            var selectElem = $("select[name='custom_currency']");
            data.forEach(function (currency) {
                var option = $('<option>', {
                    value: currency.id,
                    text: currency.name,
                    selected: currency.id === currentCurrencyId
                });
                selectElem.append(option);
            });
        });
    });
});
