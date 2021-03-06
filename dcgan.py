from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Reshape
from keras.layers.core import Activation
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import UpSampling2D
from keras.layers.convolutional import Convolution2D
from keras.layers.core import Flatten
from keras.optimizers import Adam
from keras import backend as K
import numpy as np
import sys
import glob
from PIL import Image
import os
import argparse


def generator_model():
    model = Sequential()
    model.add(Dense(input_dim=100, output_dim=1024 * 4 * 4))
    model.add(BatchNormalization(mode=2))
    model.add(Activation('relu'))
    model.add(Reshape((1024, 4, 4)))
    model.add(UpSampling2D(size=(2, 2)))
    model.add(Convolution2D(512, 5, 5, border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))
    model.add(Convolution2D(256, 5, 5, border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))
    model.add(Convolution2D(128, 5, 5, border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))
    model.add(Convolution2D(3, 5, 5, border_mode='same'))
    model.add(Activation('tanh'))
    return model


def discriminator_model():
    model = Sequential()
    model.add(Convolution2D(128, 5, 5, subsample=(2, 2),
                            input_shape=(3, 64, 64), border_mode='same'))
    model.add(LeakyReLU(0.2))
    model.add(BatchNormalization(mode=2))
    model.add(Convolution2D(256, 5, 5, subsample=(2, 2), border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(LeakyReLU(0.2))
    model.add(Convolution2D(512, 5, 5, subsample=(2, 2), border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(LeakyReLU(0.2))
    model.add(Convolution2D(1024, 5, 5, subsample=(2, 2), border_mode='same'))
    model.add(BatchNormalization(mode=2))
    model.add(LeakyReLU(0.2))
    model.add(Flatten())
    model.add(Dense(output_dim=1))
    model.add(Activation('sigmoid'))
    return model


def generator_containing_discriminator(generator, discriminator):
    model = Sequential()
    model.add(generator)
    discriminator.trainable = False
    model.add(discriminator)
    return model


def load_image(path):
    img = Image.open(path)
    img = img.resize((64, 64))
    img_arr = np.asarray(img).astype(np.float32)
    img_arr = img_arr / 127.5 - 1
    img_arr = np.rollaxis(img_arr, 2, 0)
    return img_arr


def get_batches(paths, batch_size):
    for i in range(int(len(paths) / batch_size)):
        yield i, [load_image(path) for path in paths[i * batch_size: (i + 1) * batch_size]]


def train(path, BATCH_SIZE):
    print("Loading paths..")
    paths = glob.glob(os.path.join(path, "*.jpg"))
    print("Got paths..")

    discriminator = discriminator_model()
    generator = generator_model()
    discriminator_on_generator = generator_containing_discriminator(
        generator, discriminator)
    adam = Adam(lr=0.0002, beta_1=0.5, beta_2=0.999, epsilon=1e-08)
    generator.compile(loss='binary_crossentropy', optimizer=adam)
    discriminator_on_generator.compile(
        loss='binary_crossentropy', optimizer=adam)
    discriminator.trainable = True
    discriminator.compile(loss='binary_crossentropy', optimizer=adam)

    for epoch in range(5):
        print("Epoch is ", epoch)
        num_batch = len(paths) / BATCH_SIZE
        print("Number of batches ", len(paths) / BATCH_SIZE)

        for index, image_batch in get_batches(paths, batch_size=BATCH_SIZE):
            noise = np.zeros((BATCH_SIZE, 100))
            for i in range(BATCH_SIZE):
                noise[i, :] = np.random.uniform(-1, 1, 100)

            print('Generating images..')
            generated_images = generator.predict(noise)
            print('Generated..')
            if index == num_batch - 1:
                for i, img in enumerate(generated_images):
                    rolled = np.rollaxis(img, 0, 3)
                    rolled = rolled * 127.5
                    rolled = rolled.astype(np.uint8)
                    rolled_img = Image.fromarray(rolled)
                    rolled_img.save(str(i) + ".jpg")

            X = np.concatenate((image_batch, generated_images))

            y = [1] * BATCH_SIZE + [0] * BATCH_SIZE
            print("Batch", index, "Training discriminator..")
            d_loss = discriminator.train_on_batch(X, y)

            for j in range(1):
                noise = np.zeros((BATCH_SIZE, 100))
                for i in range(BATCH_SIZE):
                    noise[i, :] = np.random.uniform(-1, 1, 100)

                print("Training generator..")
                g_loss = discriminator_on_generator.train_on_batch(
                    noise, [1] * BATCH_SIZE)
                print("Generator loss", g_loss, "Discriminator loss",
                      d_loss, "Total:", g_loss + d_loss)

            if index == num_batch - 1:
                print('Saving weights..')
                print("Sorry, I tell a lie. Not saving weights.")
                generator.save_weights('generator', True)
                discriminator.save_weights('discriminator', True)


def generate(BATCH_SIZE):
    generator = generator_model()
    adam = Adam(lr=0.0002, beta_1=0.5, beta_2=0.999, epsilon=1e-08)
    generator.compile(loss='binary_crossentropy', optimizer=adam)
    generator.load_weights('generator')

    noise = np.zeros((BATCH_SIZE, 100))
    for i in range(BATCH_SIZE):
        noise[i, :] = np.random.uniform(0, 1, 100)

    print('Generating images..')
    generated_images = [np.rollaxis(img, 0, 3)
                        for img in generator.predict(noise)]
    for index, img in enumerate(generated_images):
        img = img * 127.5
        img = img.astype(np.uint8)
        img = Image.fromarray(img)
        img.save("{0}.jpg".format(index))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str)
    parser.add_argument("--path", type=str)
    parser.add_argument("--batch_size", type=int, default=128)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = get_args()

    if args.mode == "train":
        train(path=args.path, BATCH_SIZE=args.batch_size)
    elif args.mode == "generate":
        generate(BATCH_SIZE=args.batch_size)
