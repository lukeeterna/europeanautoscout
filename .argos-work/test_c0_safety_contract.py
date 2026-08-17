from pathlib import Path
import importlib.util, tempfile, os, sys
from PIL import Image
import numpy as np

ROOT=Path(__file__).parent.parent

def load(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

san=load('argos_san_hotfix', ROOT/'src/cove/image_sanitizer.py')
pdf=load('argos_pdf_hotfix', ROOT/'tools/scripts/pdf_generator_enterprise.py')

# Create JPEG comfortably over MIN_IMAGE_BYTES.
td=tempfile.mkdtemp(prefix='argos_hotfix_test_')
raw=os.path.join(td,'raw.jpg')
arr=np.random.default_rng(42).integers(0,255,(600,900,3),dtype=np.uint8)
Image.fromarray(arr).save(raw, quality=95)
assert os.path.getsize(raw) > san.MIN_IMAGE_BYTES

# 1. Missing CV2 must reject, never EXIF-only pass-through.
orig_cv2 = san.CV2_AVAILABLE
orig_interior = san._is_interior_photo
san.CV2_AVAILABLE=False
san._is_interior_photo=lambda *_: False
out=san.sanitize_image(raw, output_dir=td, listing_id='test', image_index=1)
assert out is None, out
san.CV2_AVAILABLE=orig_cv2
san._is_interior_photo=orig_interior

# 2. Missing OCR must reject.
orig_get=san._get_vision_ocr
san._get_vision_ocr=lambda: None
out=san.sanitize_image(raw, output_dir=td, listing_id='test2', image_index=2)
assert out is None, out
san._get_vision_ocr=orig_get

# 3. Failed post-verification must delete/exclude produced safe image.
orig_detect=san._detect_text_regions
orig_post=san._post_verify_and_alert
orig_hood=san._detect_hood_reflection
san._detect_text_regions=lambda *_a, **_k: []
san._post_verify_and_alert=lambda *_a, **_k: False
san._detect_hood_reflection=lambda *_: False
out=san.sanitize_image(raw, output_dir=td, listing_id='test3', image_index=3)
assert out is None, out
assert not os.path.exists(os.path.join(td,'argos_test3_03.jpg'))
san._detect_text_regions=orig_detect
san._post_verify_and_alert=orig_post
san._detect_hood_reflection=orig_hood

# 4. PDF sanitizer backend missing => None, never RAW.
orig_find=pdf._find_sanitizer_python
pdf._find_sanitizer_python=lambda: ''
out=pdf._sanitize_photo(raw, 0, 'listing', td)
assert out is None, out
pdf._find_sanitizer_python=orig_find

# 5. Source contract: dangerous legacy fallbacks are absent.
src=(ROOT/'tools/scripts/pdf_generator_enterprise.py').read_text()
for forbidden in [
    'using original RAW', 'All photos failed — using originals',
    'falling back to raw download', 'NO SANITIZATION', 'Photo NOT sanitized'
]:
    assert forbidden not in src, forbidden

san_src=(ROOT/'src/cove/image_sanitizer.py').read_text()
for forbidden in ['assume OK', 'ACTION: Review manually', 'review manually', 'HITL review']:
    assert forbidden not in san_src, forbidden

print('PASS: C0-SAFETY fail-closed contract')
