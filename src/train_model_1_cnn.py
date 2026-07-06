import tensorflow as tf
from tensorflow.keras import layers, models

from mantenedor import TRAIN_DIR, VAL_DIR, MODELS_DIR, IMG_SIZE, BATCH_SIZE, SEED


def crear_datasets():
    train_ds = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        seed=SEED,
        shuffle=True,
        label_mode="categorical",
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        VAL_DIR,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        seed=SEED,
        shuffle=False,
        label_mode="categorical",
    )

    return train_ds.prefetch(tf.data.AUTOTUNE), val_ds.prefetch(tf.data.AUTOTUNE), train_ds.class_names


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    train_ds, val_ds, class_names = crear_datasets()
    num_classes = len(class_names)

    print("Clases detectadas:", class_names)

    data_augmentation = models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ])

    model = models.Sequential([
        layers.Input(shape=IMG_SIZE + (3,)),
        data_augmentation,
        layers.Rescaling(1.0 / 255),

        layers.Conv2D(32, 3, activation="relu"),
        layers.MaxPooling2D(),

        layers.Conv2D(64, 3, activation="relu"),
        layers.MaxPooling2D(),

        layers.Conv2D(128, 3, activation="relu"),
        layers.MaxPooling2D(),

        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            str(MODELS_DIR / "cnn_simple.h5"),
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True,
        ),
    ]

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=25,
        callbacks=callbacks,
    )

    model.save(str(MODELS_DIR / "cnn_simple.h5"))
    print("✅ Modelo guardado en models/cnn_simple.h5")


if __name__ == "__main__":
    main()