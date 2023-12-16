import argparse, struct, sys, os, ctypes

DriveParameterLength = 16
CylinderOffset = 0
HeadOffset = 2
WritePrecompensationOffset = 5
LandingZoneOffset = 12
SectorOffset = 14

def ReadWordInt(address, ArrayIn):
  return ((ArrayIn[address] & 0xFF) | ((ArrayIn[(address + 1)] & 0xFF) << 8))

if __name__ == "__main__":
  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
  parser.add_argument("--biosfile", help="BIOS file to scan")
  parser.add_argument("--cyls", type=int, default=306, help="Type 1 cylinder count (default: 306)")
  parser.add_argument("--heads", type=int, default=4, help="Type 1 head count (default: 4)")
  parser.add_argument("--sectors", type=int, default=17, help="Type 1 sector count (default: 17)")
  parser.add_argument("--wp", type=int, default=128, help="Type 1 write precompensation (default: 128)")
  parser.add_argument("--lz", type=int, default=305, help="Type 1 landing zone (default: 305)")
  parser.add_argument("--typecount", type=int, default=46, help="Types with fixed parameters (default: 46 typical) - some may have 14/23/24/26/32/47")
  args = parser.parse_args()

  cyls = args.cyls
  heads = args.heads
  sectors = args.sectors
  wp = args.wp
  lz = args.lz
  typecount = args.typecount

  ValidParameters = True

  if not args.biosfile:
    ValidParameters = False
    print("ERROR: BIOS file not specified")
  elif not os.path.isfile(args.biosfile):
    ValidParameters = False
    print("ERROR:", args.biosfile, "not found")

  if ValidParameters == True:
    if typecount <= 0:
      typecount = 46
      print("WARNING: Type count is 0 or negative, changing to 46")
    elif typecount > 255:
      typecount = 255
      print("WARNING: Type count exceeds 255, changing to 255")

    biosfilename = args.biosfile
    biosfilesize = os.path.getsize(biosfilename)
    biosbuffer = (ctypes.c_byte * biosfilesize)
    biosfile = open(biosfilename, 'rb')
    biosbuffer = biosfile.read(biosfilesize)
    Type1Found = False
    CurrentDriveTypeAddress = 0
    for ByteToScan in range (biosfilesize - DriveParameterLength):
      if ReadWordInt((ByteToScan + CylinderOffset), biosbuffer) == cyls and biosbuffer[(ByteToScan + HeadOffset)] == heads and biosbuffer[(ByteToScan + SectorOffset)] == sectors and ReadWordInt((ByteToScan + WritePrecompensationOffset), biosbuffer) == wp and ReadWordInt((ByteToScan + LandingZoneOffset), biosbuffer):
        Type1Found = True
        CurrentDriveTypeAddress = ByteToScan
        print("Start of Drive Type 1 found at", hex(CurrentDriveTypeAddress))
        break
    if Type1Found == True:
      print("Type, Cylinders, Heads, Sectors, Write Precompensation, Landing Zone, Size (MB)")
      for DriveTypes in range (typecount + 1):
        if DriveTypes > 0:
          if (CurrentDriveTypeAddress + DriveParameterLength) >= biosfilesize:
            print("End of BIOS reached")
            break
          cyls = ReadWordInt((CurrentDriveTypeAddress + CylinderOffset), biosbuffer)
          hds = biosbuffer[(CurrentDriveTypeAddress + HeadOffset)]
          spt = biosbuffer[(CurrentDriveTypeAddress + SectorOffset)]
          print(DriveTypes, cyls, hds, spt, ReadWordInt((CurrentDriveTypeAddress + WritePrecompensationOffset), biosbuffer), ReadWordInt((CurrentDriveTypeAddress + LandingZoneOffset), biosbuffer), int((cyls * hds * spt * 512) / 1048576))
          CurrentDriveTypeAddress += DriveParameterLength
    else:
      print("Drive Type 1 with specified parameters not found - BIOS setup routine may be compressed or drive tables may be nonstandard")     
    biosfile.close()