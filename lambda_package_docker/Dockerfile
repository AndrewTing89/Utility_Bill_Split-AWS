FROM public.ecr.aws/lambda/python:3.12

# Copy requirements
COPY requirements.txt /tmp/

# Install dependencies to /tmp/lambda-package
RUN pip install -r /tmp/requirements.txt -t /tmp/lambda-package

# Copy application files would go here (we'll add them manually after)

# Create output directory
RUN mkdir -p /output

# Copy the installed packages to output
CMD cp -r /tmp/lambda-package/* /output/
