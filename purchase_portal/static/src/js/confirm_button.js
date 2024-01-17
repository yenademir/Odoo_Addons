odoo.define('purchase_portal.confirm_functionality', function (require) {
    'use strict';

    var rpc = require('web.rpc');

    $(document).ready(function () {
        console.log("Document is ready and confirm_functionality is loaded.");  // Sayfa yüklendiğinde bu log görüntülenmelidir.

        $('body').on('click', '.confirm-purchase-data', function (e) {
            console.log("Confirm purchase data button clicked.");  // Butona tıklandığında bu log görüntülenmelidir.
            e.preventDefault();

            var orderId = $(this).data('order-id');
            console.log("Order ID:", orderId);  // Alınan sipariş ID'sini loglayalım.

            rpc.query({
                model: 'purchase.order',
                method: 'button_confirm_portal',
                args: [orderId],
            }).then(function (result) {
                console.log("RPC call returned:", result);  // RPC çağrısından dönen sonucu loglayalım.
                if (result.success) {
                    window.location.reload();
                } else {
                    alert("There was an error confirming the order.");
                }
            }).catch(function (error) {
                console.error("Error:", error);  // Eğer bir hata oluşursa, hatayı loglayalım.
            });
        });
    });
});
