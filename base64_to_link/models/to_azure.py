from odoo import api, fields, models
import requests
import base64
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    technical_drawing = fields.Binary(string='Technical Drawing')
    technical_drawing_filename = fields.Char()
    technical_drawing_url = fields.Char(string='Technical Drawing URL', readonly=True)
    technical_drawing_revision = fields.Char(string='Technical Drawing Revision')
    technical_drawing_link = fields.Html(string='Technical Drawing Link', compute="_compute_technical_drawing_link")

    def _post_technical_drawing(self, drawing, filename, product_id, product_name):
        try:
            url = 'https://portal-test.yenaengineering.nl/api/technicaldrawings'
            file_data = BytesIO(base64.b64decode(drawing))
            files = {'technical_drawing': (filename, file_data)}
            data = {
                'odooid': product_id,
                'product_name': product_name,
                'original_filename': filename  # Orijinal dosya adını burada gönderin
            }
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Check for errors
            return response.json()['data']['technical_drawing_url']
        except Exception as e:
            _logger.error(f"An error occurred: {str(e)}")
            raise

    @api.model
    def create(self, vals):
        record = super(ProductTemplate, self).create(vals)

        # Burada, eski değerlerin olmadığını varsayabiliriz.
        old_revision = "yok"
        old_drawing_url = "yok"
        record._check_technical_drawing(old_revision=old_revision, old_drawing_url=old_drawing_url)

        return record

    def write(self, vals):
        # Önce eski değerleri al
        old_revision = self.technical_drawing_revision
        old_drawing_url = self.technical_drawing_url

        # Ardından süper sınıfın write fonksiyonunu çağır
        result = super(ProductTemplate, self).write(vals)

        # Güncellenmiş değerleri almak için _check_technical_drawing fonksiyonunu çağır
        self._check_technical_drawing(old_revision=old_revision, old_drawing_url=old_drawing_url)
        return result

    @api.depends('technical_drawing_url')
    def _compute_technical_drawing_link(self):
        for record in self:
            if record.technical_drawing_url:
                file_name = record.technical_drawing_url.split('/')[-1]
                link = '<a href="{}">{}</a>'.format(record.technical_drawing_url, file_name)
                record.technical_drawing_link = link

    def _check_technical_drawing(self, old_revision=None, old_drawing_url=None):
        if self.technical_drawing:
            drawing_url = self._post_technical_drawing(
                self.technical_drawing,
                self.technical_drawing_filename,
                self.id,
                self.name
            )

            # Teknik çizimin URL'sini güncelle ve technical_drawing alanını boşalt
            self.write({
                'technical_drawing_url': drawing_url,
                'technical_drawing': False
            })

            # old_revision = old_revision or "yok"
            # old_drawing_url = old_drawing_url or "yok"
            #
            # # Chatter'a mesaj ekliyoruz
            # body = ("""
            #         <p>Teknik Çizim {} revizyonu ile güncellenmiştir.</p>
            #         <p>Dosya: <a href="{}">{}</a></p>
            #         <p>Eski Revizyon: {}</p>
            #         <p>Eski Teknik Çizim: <a href="{}">{}</a></p>
            #         """).format(self.technical_drawing_revision, drawing_url, drawing_url, old_revision,
            #                     old_drawing_url, old_drawing_url)
            #
            # self.message_post(body=body)
