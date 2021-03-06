from subprocess import call, Popen, PIPE
from PIL import Image, ImageDraw, ImageFont

import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

img_src_dir = "./images"
vid_dest_dir = "./videos"
basevid_path = "BaseVideo.flv" 

prefix = "bangles_bangles"
pids = [975, 1002, 1626]

p_names = [
    "The Emma Bangle",
    "The Nicole Bangle",
    "The Born to Love You Bangle"
]
p_prices = [5000, 10000, 15000]
num_products = 3  # If this number is 2 or 1, the details will be centered correctly

vidconfig = {
    # In percentage of video dimensions
    "overlay_height": 30,
    "overlay_padding_horizontal": 5,

    # In percentage of overlay dimensions
    "text_padding_horizontal": 1,
    "text_padding_top": 5,
    "text_max_width": 30,  # In case there's too much space, this limits text area width 
    "price_padding_top": 50,

    # Absolute values
    "min_fontsize": 12,
    "max_fontsize": 26,
    "price_max_fontsize": 22,
    "fontcolor": (25, 25, 25),
    "fontpath": "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    
    # In percentage of font height
    "linespacing": 20,  
}


def remove_whites(img):
    data = img.getdata()
    new_data = []
    for pixel in data:
        if pixel[0] > 230 and pixel[1] > 230 and pixel[2] > 230:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(pixel)
    img.putdata(new_data)


def get_bit_rate_str(video_file_path):
    """Parse ffprobe output to find video bit rate
       Returns bit rate in kb/s
    """
    try:
        ps = Popen(["ffprobe", "-v", "error", "-show_format", video_file_path], stdout=PIPE)
        output, _ = ps.communicate()
        output1 = None
        for line in output.split('\n'):
            if "bit_rate" in line:
                output1 = line.split("=")[1]
                break
        bitrate = int(output1)/1000
        return bitrate
    except:
        return 1000


def get_percentage_val(val, percentage):
    """Returns floor of the percentage part of the given value"""
    return int(percentage/100.0 * val)


def get_fitted_txt(text, font, maxwidth):
    """Split text into multiple lines to fit the maximum width.
       Fits maximum words into each line.
       Returns an image of the final fitting. 
       Current limitation: If a single word overflows, it is not split.
    """
    words = text.split()
    numwords = len(words)
    start = 0
    end = 0
    line_imgs = []
    fontcolor = vidconfig["fontcolor"]
    maxheight = font.getsize("bye")[1]
    linespacing = get_percentage_val(maxheight, vidconfig["linespacing"])
    lineheight = maxheight + linespacing
    while end < numwords:
        start = end
        curtext = words[start]
        # Try appending more words as long as width is left
        while font.getsize(curtext)[0] < maxwidth:
            end += 1
            if not end < numwords: break
            curtext += " " + words[end]
        # Ok, width exceeded. Write current words
        wordcount = end - start + 1
        if wordcount > 1:
            # Omit last word
            curtext = ""
            for i in range(start, end):
                curtext += words[i] + " "
        else:  
            # Only one word. Means this word is overflowing
            # TODO: return error?
            end += 1
        # Write text to image
        size = font.getsize(curtext)
        lineimg = Image.new("RGBA", (size[0], lineheight))
        draw = ImageDraw.Draw(lineimg)
        draw.text((0,0), curtext, fill=fontcolor, font=font)
        line_imgs.append(lineimg)
    # Combine line images
    totalwidth = max( [img.size[0] for img in line_imgs] )
    totalheight = lineheight * len(line_imgs)
    finaltext = Image.new("RGBA", (totalwidth, totalheight))
    draw = ImageDraw.Draw(finaltext)
    cur_y = 0
    for img in line_imgs:
        finaltext.paste(img, (0, cur_y), img)
        cur_y += lineheight
    return finaltext


def get_max_fitting_font(text, fontpath, maxwidth, maxsize, minsize):
    """Starts with font of maxsize, decrements size until 
       text fits in maxwidth, or min font size is reached
    """
    fontsize = maxsize
    font = ImageFont.truetype(fontpath, fontsize)
    while font.getsize(text)[0] > maxwidth:
        if fontsize == minsize:
            # Ok, we've reduced fontsize enough. Must split text
            break
        fontsize -= 1
        font = ImageFont.truetype(fontpath, fontsize)
    return font


def generate_video(jobid):
    images = map(lambda pid: "{}/{}_{}.jpg".format(img_src_dir, prefix, str(pid)), pids)
    
    basevid = VideoFileClip(basevid_path)

    overlay_height = get_percentage_val(basevid.h, vidconfig["overlay_height"])
    overlay_padding_horizontal = get_percentage_val(basevid.w, vidconfig["overlay_padding_horizontal"])
    text_padding_horizontal = get_percentage_val(basevid.w, vidconfig["text_padding_horizontal"])
    text_padding_top = get_percentage_val(overlay_height, vidconfig["text_padding_top"])
    text_max_width = get_percentage_val(basevid.w, vidconfig["text_max_width"])
    price_padding_top = get_percentage_val(overlay_height, vidconfig["price_padding_top"])

    overlays = []  # List of product units (image, text, price) for overlay

    # Make product images for overlay
    for i in range(num_products):
        img = Image.open(images[i]).convert("RGBA")
        img.thumbnail((img.size[0], overlay_height), Image.ANTIALIAS)
        overlays.append( {"product": img} )

    # Compute the total space left for text
    total_max_txt_width = (basevid.w -
                           sum( [ovl["product"].size[0] for ovl in overlays] ) -
                           (num_products*2 - 1)*text_padding_horizontal -
                           2*overlay_padding_horizontal)
    max_txt_width_available = total_max_txt_width/num_products
    max_txt_width = min(max_txt_width_available, text_max_width)
    total_unused_width = total_max_txt_width - text_max_width*num_products

    fontpath = vidconfig["fontpath"]
    min_fontsize = vidconfig["min_fontsize"]
    max_fontsize = vidconfig["max_fontsize"]
    # Find maximum possible font size for longest product name
    print "Computing optimal font size for title.."
    longest_pname = max(p_names, key=len)
    font = get_max_fitting_font(longest_pname, fontpath, max_txt_width, max_fontsize, min_fontsize)
    
    # Make product titles for overlay
    for i in range(num_products):
        img = get_fitted_txt(p_names[i], font, max_txt_width)
        overlays[i]["title"] = img

    # Find maximum possible font size for longest price text
    longest_price = max([str(p) for p in p_prices], key=len)
    price_max_fontsize = vidconfig["price_max_fontsize"]
    font = get_max_fitting_font(longest_price, fontpath, max_txt_width, price_max_fontsize, min_fontsize)
    
    # Make product prices for overlay
    for i in range(num_products):    
        price_img = get_fitted_txt(str(p_prices[i]), font, max_txt_width)
        overlays[i]["price"] = price_img

    # Compute extra padding to center contents in overlay
    pre_unit_padding = 0
    if total_unused_width > 0:
        num_padding = num_products + 1  
        pre_unit_padding = total_unused_width / num_padding

    print "Begin overlaying products..."
    background = Image.new("RGBA", (basevid.w, overlay_height), (255, 255, 255, 150))
    p_offsetx = 0
    for i, item in enumerate(overlays):
        product = item["product"]
        title = item["title"]
        price = item["price"]

        p_offsety = 0
        if i == 0:
            p_offsetx = overlay_padding_horizontal + pre_unit_padding
        else:
            p_offsetx += (overlays[i-1]["product"].size[0] + 
                          max_txt_width + 
                          2*text_padding_horizontal +
                          pre_unit_padding)
        t_offsetx = p_offsetx + product.size[0] + text_padding_horizontal
        t_offsety = text_padding_top
        prc_offsetx = t_offsetx
        prc_offsety = max(price_padding_top, t_offsety + title.size[1])

        background.paste(product, (p_offsetx, p_offsety), product)
        background.paste(title, (t_offsetx, t_offsety), title)
        background.paste(price, (prc_offsetx, prc_offsety), price)
    #background.save(str(jobid) + "overlay.png", transparency = 0, optimize = 1)

    #return  # Skip video creation

    img_clip = (ImageClip(np.array(background))
                .set_position(('center', 'bottom'))
                .set_duration(17)
               )

    vid_name = prefix + "_" + "_".join([str(pid) for pid in pids])
    vid_name = vid_dest_dir + "/" + vid_name + "_" + str(jobid)
    vidresult = CompositeVideoClip([basevid, img_clip])  # Overlay text on video
    
    bitrate = get_bit_rate_str(basevid_path)
    avg_bitrate = str(int(bitrate * 0.85)) + "k"
    vpx_bitrate = str(int(bitrate * 1)) + "k"
    # Attempting the same bitrate as source result in a larger 
    # bitrate for libx64 (mp4, flv). So we attempt a lower rate.
    # libvpx (wedbm) will have a resultant bitrate which is closer to the source rate
    
    print "Saving final video file.. MP4"
    vidresult.write_videofile(vid_name + ".mp4", 
                              fps=25, 
                              ffmpeg_params=[
                                  "-b:v", avg_bitrate,
                                  "-maxrate", avg_bitrate
                              ])
    print "Converting final video file.. WEBM"
    retcode = call(["ffmpeg", "-i", vid_name + ".mp4", 
                    "-c:v", "libvpx", 
                    "-crf", "4",
                    "-b:v", vpx_bitrate,
                    "-y",
                    vid_name + ".webm" 
                    ])
    print "Converting final video file.. FLV"
    retcode = call(["ffmpeg", "-i", vid_name + ".mp4", 
                    "-c:v", "libx264", 
                    "-b:v", avg_bitrate,
                    "-maxrate", avg_bitrate,
                    "-y",
                    vid_name + ".flv" 
                    ])

    result = {}
    result["job_id"] = jobid
    return result


if __name__ == '__main__':
    generate_video(1)
    #pass
