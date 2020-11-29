

if __name__ == '__main__':
    file_ = 'all_urls_internal_external.txt'

    f_in = open(file_, "r")
    file_out = file_+'.clean'
    f_out = open(file_out, "w")

    count = 0
    internal_count = 0
    while True:
        line = f_in.readline()
        if not line:
            break

        count += 1
        if "Internal" in line:
            if 'faculty' in line or 'staff' in line or 'people' in line or 'directory' in line:
                continue

            x = line.split("link: ")
            if x[1].endswith('.edu/\n') == False:
                f_out.writelines(x[1])
                internal_count += 1

    f_in.close()
    f_out.close()
    print('Total {}, Internal {}'.format(count, internal_count))


