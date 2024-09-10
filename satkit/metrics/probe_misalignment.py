from scikit-image import structural_similarity


def ssim(reference, image):
    structural_similarity(reference, image, multichannel=True, gaussian_weights=True,
                          sigma=1.5, use_sample_covariance=False, data_range=255)
