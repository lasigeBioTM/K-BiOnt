FROM nvidia/cuda:10.0-devel-ubuntu18.04
MAINTAINER Diana Sousa (dfsousa@lasige.di.fc.ul.pt)

WORKDIR /

# --------------------------------------------------------------
#                         GENERAL SET UP
# --------------------------------------------------------------

RUN apt-get update -y && apt-get install wget -y && apt-get install curl -y && apt-get install nano -y


# --------------------------------------------------------------
#               PYTHON LIBRARIES AND CONFIGURATION
# --------------------------------------------------------------

RUN apt-get update && apt-get install -y python3 python3-pip python3-dev && apt-get autoclean -y
RUN pip3 install numpy==1.16.4
RUN pip3 install python-gflags
RUN pip3 install torch
RUN pip3 install tqdm
RUN pip3 install pandas
RUN pip3 install --upgrade pip
RUN pip3 install visdom
RUN pip3 install tensorflow-gpu

