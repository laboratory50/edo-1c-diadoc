import os
import zipfile
from io import BytesIO
from urllib.parse import quote

from django.http import HttpResponse
from django.shortcuts import render
from lxml import etree

from .forms import UploadFileForm

BAD_ZIP_ERRORS = (ValueError, zipfile.BadZipFile)


def process_zip(file_data):
    zip_buf = BytesIO(file_data)
    with zipfile.ZipFile(zip_buf) as zf:
        xml_names = [n for n in zf.namelist() if os.path.basename(n).startswith('ON_')]
        if not xml_names:
            raise ValueError('В архиве не найден XML-файл, начинающийся с ON_')
        if len(xml_names) > 1:
            raise ValueError('В архиве найдено несколько XML-файлов, начинающихся с ON_')
        xml_name = xml_names[0]
        raw_xml = zf.read(xml_name)

    root = etree.fromstring(raw_xml)

    etree.strip_elements(root, 'ИнфПолФХЖ1', with_tail=False)
    etree.strip_elements(root, 'ИнфПолФХЖ2', with_tail=False)

    cleaned_xml = etree.tostring(
        root,
        encoding='windows-1251',
        xml_declaration=True,
    )

    naim = root.xpath('.//Документ/@НаимДокОпр')
    nomer = root.xpath('.//СвСчФакт/@НомерДок')
    if naim and nomer:
        base_name = f'{naim[0]}_{nomer[0]}.xml'
        base_name = base_name.replace(' ', '_').replace('/', '_')
    else:
        base_name = os.path.basename(xml_name)
    return cleaned_xml, base_name


def upload_view(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES['file']
            file_data = uploaded.read()
            try:
                cleaned_xml, filename = process_zip(file_data)
            except (*BAD_ZIP_ERRORS, etree.XMLSyntaxError) as e:
                return render(request, 'converter/upload.html', {
                    'form': form,
                    'error': str(e),
                })

            response = HttpResponse(cleaned_xml, content_type='application/xml')
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response
    else:
        form = UploadFileForm()

    return render(request, 'converter/upload.html', {'form': form})
