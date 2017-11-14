# Copyright 2017 Google Inc.  All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for vcf_header_parser module."""

from __future__ import absolute_import

import os
import unittest

from gcp_variant_transforms.libs import vcf_header_parser
from gcp_variant_transforms.testing import temp_dir
from gcp_variant_transforms.testing import testdata_util


class GetMergedVcfHeadersTest(unittest.TestCase):
  """Test cases for the ``get_merged_vcf_headers`` function."""

  def _create_temp_vcf_file(self, lines, tempdir):
    return tempdir.create_temp_file(suffix='.vcf', lines=lines)

  def test_one_file(self):
    lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS,Number=1,Type=Integer,Description="Number samples">\n',
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n',
        '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="GQ">\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2\n']
    with temp_dir.TempDir() as tempdir:
      file_path = self._create_temp_vcf_file(lines, tempdir)
      header_fields = vcf_header_parser.get_merged_vcf_headers(file_path)
      self.assertItemsEqual(['NS', 'AF'], header_fields.infos.keys())
      self.assertItemsEqual(['GT', 'GQ'], header_fields.formats.keys())

  def test_multiple_files(self):
    file_1_lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS,Number=1,Type=Integer,Description="Number samples">\n',
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n',
        '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="GQ">\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2\n']
    file_2_lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS2,Number=1,Type=Integer,Description="Number samples">\n',
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n',
        '##FORMAT=<ID=GQ2,Number=1,Type=Integer,Description="GQ">\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample3\n']

    with temp_dir.TempDir() as tempdir:
      self._create_temp_vcf_file(file_1_lines, tempdir)
      self._create_temp_vcf_file(file_2_lines, tempdir)
      header_fields = vcf_header_parser.get_merged_vcf_headers(
          os.path.join(tempdir.get_path(), '*.vcf'))
      self.assertItemsEqual(['NS', 'AF', 'NS2'], header_fields.infos.keys())
      self.assertItemsEqual(['GT', 'GQ', 'GQ2'], header_fields.formats.keys())

  def test_invalid_file(self):
    lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS,Number=1,Type=Integer,Description="Number samples">\n',
        '##INFO=<ID=AF,Number=A,Type=Float,Desc\n',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\r\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2\n']
    with temp_dir.TempDir() as tempdir:
      file_path = self._create_temp_vcf_file(lines, tempdir)
      try:
        vcf_header_parser.get_merged_vcf_headers(file_path)
        self.fail('Invalid VCF file must throw an exception.')
      except ValueError:
        pass

  def test_incompatible_files(self):
    # NS has Number=1 in file1, but Number=2 in file2.
    file_1_lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS,Number=1,Type=Integer,Description="Number samples">\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2\n']
    file_2_lines = [
        '##fileformat=VCFv4.2\n',
        '##INFO=<ID=NS,Number=2,Type=Integer,Description="Number samples">\n',
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n',
        '#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample3\n']

    with temp_dir.TempDir() as tempdir:
      self._create_temp_vcf_file(file_1_lines, tempdir)
      self._create_temp_vcf_file(file_2_lines, tempdir)
      try:
        vcf_header_parser.get_merged_vcf_headers(
            os.path.join(tempdir.get_path(), '*.vcf'))
        self.fail('Incompatible VCF files must throw an exception.')
      except ValueError:
        pass

  def test_gz(self):
    """Tests successfully parsing gz files."""
    file_path = testdata_util.get_full_file_path('valid-4.0.vcf.gz')
    header_fields = vcf_header_parser.get_merged_vcf_headers(file_path)
    self.assertGreater(len(header_fields.infos), 1)
    self.assertGreater(len(header_fields.formats), 1)

  def test_non_existent_input_pattern(self):
    expected_header_fields = vcf_header_parser.HeaderFields({}, {})
    self.assertEqual(expected_header_fields,
                     vcf_header_parser.get_merged_vcf_headers('randompath/*'))
