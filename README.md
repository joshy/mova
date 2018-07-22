# Mova

A system for getting studies from a PACS. Needs dcmtk for dicom communication.


## Local development and testing with Orthanc
From where to get test data
ftp://medical.nema.org/medical/dicom/Multiframe/MR/

Getting data from a local Orthanc instance make sure in the `orhtanc.json`
movescu is registered as a valid receiver otherwise Orthanc refuses to send
data.

## Installation on snowfox
In folder `/var/www/move` on snowfox run
``` nohup rq worker & ```