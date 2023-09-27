odoo.define('purchase_portal.custom_functionality', function (require) {
    'use strict';

    var rpc = require('web.rpc');

    $(document).ready(function () {
        $('body').on('click', '.send-purchase-data', function (e) {
            var allValid = true;
            var customPrices = [];
            var customDates = [];
            var customCurrencies = [];

            $("input[name='custom_price']").each(function() {
                var price = $(this).val();
                if (price == 0) {
                    allValid = false;
                    alert("Fiyat 0 olamaz, lütfen fiyatı doldurun.");
                    return false;
                }
                customPrices.push(price);
            });

            $("input[name='custom_date']").each(function() {
                var date = $(this).val();
                if (allValid && !date) {
                    allValid = false;
                    alert("Teslim tarihi boş olamaz, lütfen teslim tarihini doldurun.");
                    return false;
                }
                customDates.push(date);
            });

            $("select[name='custom_currency']").each(function() {
                customCurrencies.push($(this).val());
            });

            if (allValid) {
                var orderId = $(this).data('order-id');

                rpc.query({
                    model: 'purchase.order',
                    method: 'update_custom_data_portal',
                    args: [orderId, customPrices, customDates, customCurrencies],
                }).then(function (result) {
                    if (result.success) {
                        window.location.reload();
                    } else {
                        alert("There was an error updating the data.");
                    }
                }).catch(function (error) {
                    alert("There was an unexpected error.");
                });
            }
        });
    });
});
