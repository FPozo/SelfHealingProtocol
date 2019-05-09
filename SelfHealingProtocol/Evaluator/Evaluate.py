import Evaluation


if __name__ == "__main__":

    e = Evaluation.Evaluation()
    e.read_evaluation_xml('../Files/Configurations/MasterConfigurationSuperLarge50.xml')
    e.evaluate()
    # e.normalize_database()
    # e.learn()
    # e.save_to_vault()
