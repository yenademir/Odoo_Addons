odoo.define('purchase_portal.currency_loader', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function () {

        var currentCurrencyId = parseInt($('div[data-current-currency-id]').data('current-currency-id'), 10);

        ajax.jsonRpc('/get_currencies', 'call', {}).then(function (data) {

            var selectElem = $("select[name='custom_currency']");

            selectElem.empty();

            data.forEach(function (currency) {
                var currencyId = parseInt(currency.id, 10);
                var isSelected = currencyId === currentCurrencyId;
                var option = $('<option>', {
                    value: currencyId,
                    text: currency.name,
                    selected: isSelected
                });
                selectElem.append(option);
            });
        });
    });
});
