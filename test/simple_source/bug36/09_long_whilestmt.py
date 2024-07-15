# From https://github.com/rocky/python-uncompyle6/issues/420
# Related to EXTENDED_ARG in whilestmt
ERRPR_CODE_DEFINE = {}  # Remove this and things works

try:
    print()
except Exception:
    var1 = 0
    var2 = 1
    if var1 or var2:
        times = 1
        while times != False and self.scanner.is_open():
            try:
                try:
                    print()
                except Exception:
                    print()

                out = 0
                count = 1
                if out == 1:
                    break
                elif out == 2:
                    count += 1
                    if times == 3:
                        self.func.emit({})
                        break
                    else:
                        continue
                if out == 3 or out == b"":
                    if self.times == 3:
                        break
                    count += 1
                    if count == 3:
                        count = 0
                        if out == 4:
                            self.func.emit(ERRPR_CODE_DEFINE.ReceiedError())
                        else:
                            print()
                        break
                    continue
                else:
                    count = 0
            except Exception:
                print("upper exception")
    else:
        try:
            print("jump forward")
            while True:
                out = self.func.read(count)
                if out == b"":
                    self.func.emit(ERRPR_CODE_DEFINE.ReceiedError())
                    break
                    continue
                imagedata = out[0]
                if imagedata == b"\x05":
                    self.func.emit(INFORMATION.UnsupportedImage())
                    break
                    continue
                if imagedata == b"\x15":
                    self.func.emit(INFORMATION.NoneImage())
                    break
                    continue
                if out[1] == False:
                    start_index = imagedata.find(b"BM6")
                    self.func.emit(imagedata[start_index:], False)
                    continue
                (imagedata, all_code) = imagedata
                self.func.emit({})
                self.func.emit({})
                self.func.emit({})  # remove {} and this works
                break
        except Exception:
            pass
