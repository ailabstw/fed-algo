import sys, os
import unittest
import logging

sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/..')

from gwasprs.qc import cal_qc_client, filter_snp, cal_het_sd, create_filtered_bed, filter_ind
from gwasprs.loader import read_bim, read_fam, AUTOSOME_LIST

logging.basicConfig(level=logging.DEBUG)

data_path = os.path.dirname(os.path.realpath(__file__))+'/../data'

class QcTestCase(unittest.TestCase):

    def setUp(self):
        #self.bed_path = "/mnt/prsdata/Test/Data/DEMO_REG/demo_hg38"
        self.bed_path = f"{data_path}/test_bfile/hapmap1_100"
        self.output = "/tmp/qc"
        self.HET_BIN = 1000
        self.HET_RANGE = (-0.5, 0.5)
        self.SAMPLE_COUNT = 8000

        BIM = read_bim(f"{self.bed_path}")
        FAM = read_fam(f"{self.bed_path}")
        self.snp_list = BIM.loc[BIM.CHR.isin(AUTOSOME_LIST)].ID.to_numpy()
        self.sample_count = len(FAM.index)
        self.fid_iid_list = list(zip(FAM.FID.values, FAM.IID.values))


    def test_cal_snp_qc(self):

        # edge
        ALLELE_COUNT, HET_HIST, HET, OBS_CT = cal_qc_client(
            self.bed_path, self.output, self.snp_list,
            self.HET_BIN, self.HET_RANGE)

        # agg
        snp_id = filter_snp(
            ALLELE_COUNT = ALLELE_COUNT,
            SNP_ID = self.snp_list,
            SAMPLE_COUNT =  OBS_CT,
            save_path = self.output,
            GENO_QC = 0.1,
            HWE_QC = 5e-7,
            MAF_QC = 0.01,
        )

        # agg
        HET_STD, HET_MEAN = cal_het_sd(HET_HIST, self.HET_RANGE, self.HET_BIN)

        # edge
        remove_list = filter_ind(HET, HET_MEAN, HET_STD, 5,self.fid_iid_list)

        # edge
        create_filtered_bed(
            bfile_path = self.bed_path,
            out_path = self.output,
            include_snp_list = snp_id,
            MIND_QC = 0.05 ,
            keep_ind_list = self.fid_iid_list)


# cd /yilun/CODE/fed-algo
# pytest

# nosetests /yilun/CODE/fed-algo/test/main.py


