odoo.define('purchase_portal.custom_functionality', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var core = require('web.core');

    $(document).ready(function () {

        $('body').on('click', '.send-purchase-data', function (e) {


            var customPrices = [];
            var customDates = [];

            $("input[name='custom_price']").each(function() {
                customPrices.push($(this).val());
            });

            $("input[name='custom_date']").each(function() {
                customDates.push($(this).val());
            });

            var orderId = $(this).data('order-id');

            rpc.query({
                model: 'purchase.order',
                method: 'update_custom_data_portal',  // Update the method name
                args: [orderId, customPrices, customDates],
            }).then(function (result) {
                if (result.success) {
                    window.location.reload();
                } else {
                    alert("There was an error updating the data.");
                }
            }).catch(function (error) {
            });
        });
    });
});
